import json
import os
from datetime import datetime

from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.ability_id import AbilityId
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2
from sc2.data import Result

from src.bot.strategy import BuildPhase, CameraMode, MAX_SATURATION_RATIO, BASE_MINERAL_RADIUS, THREAT_RANGE, ENGAGE_RANGE, GATEWAY_MINERAL_BASELINE, GATEWAY_PER_BASE, GATEWAY_MINERAL_FLOAT_THRESHOLD, GATEWAY_MINERAL_FLOAT_EXTRA, MAX_GATEWAYS, FORGE_MINERAL_THRESHOLD, UPGRADE_RESOURCE_THRESHOLD

from src.ml.observation import extract_features, extract_building_inference, extract_eco_inference
from src.ml.events import detect_events
from src.utils.logger import setup_logger, log_features
from src.utils.replay import save_replay
from src.ml.report import generate_report, generate_index

from src.bot.scout import (
    ScoutState, get_scout_waypoints, should_retreat_scout,
    compute_next_scout_move, update_scout_waypoints, ScoutMetadata,
)
from src.bot.upgrades import (
    UPGRADE_ORDER, get_next_upgrade, should_build_forge,
    should_build_twilight, get_twilight_upgrade,
)
from src.bot.decision import evaluate_decision, DecisionState, SURRENDER_MIN_TIME, SURRENDER_ARMY_VALUE_RATIO, SURRENDER_WORKER_MIN, SURRENDER_FOG_ARMY_VALUE_RATIO, VICTORY_MIN_TIME, VICTORY_ENEMY_GONE_SECONDS, VICTORY_MIN_ARMY

from src.bot.pressure import PressureLevel, assess_pressure, pressure_expand_saturation, pressure_expand_mineral_bank, pressure_gateway_bonus, pressure_gateway_float_extra
from src.strategies.types import Action, ActionType, StrategyProfile
from src.strategies.bias_calculator import BiasCalculator
from src.strategies.priority_engine import PriorityEngine
from src.strategies.loader import StrategyLoader


class MyBot(BotAI):
    MAX_WORKERS = 70
    ATTACK_SUPPLY = 200
    POLICY_MODES = {"heuristic", "ml_shadow"}

    def __init__(self, log_interval: int = 22, surrender_enabled: bool = False, fog_enabled: bool = False, strategy_profile: str | None = None, opponent_difficulty: str = "Medium", opponent_race: str = "Terran", opponent_count: int = 1, policy_mode: str = "heuristic", experiment_id: str | None = None, model_name: str | None = None, model_version: str | None = None, shadow_profiles: list[str] | None = None):
        super().__init__()
        if policy_mode not in self.POLICY_MODES:
            raise ValueError(f"Unsupported policy_mode: {policy_mode}")
        self.logger = setup_logger()
        self.log_interval = log_interval
        self.surrender_enabled = surrender_enabled
        self.fog_enabled = fog_enabled
        self.strategy_profile_name = strategy_profile
        self.opponent_difficulty = opponent_difficulty
        self.opponent_race = opponent_race
        self.opponent_count = opponent_count
        self.policy_mode = policy_mode
        self.experiment_id = experiment_id
        self.model_name = model_name
        self.model_version = model_version
        self._decision_state = DecisionState.DEFEND
        self._state_start_time: float = 0.0
        self._surrender_conditions_start: float | None = None
        self._enemy_gone_start: float | None = None
        self._surrender_fired = False
        self._last_log = 0
        self._match_id: str | None = None
        self._features_file: str | None = None
        self._events_file: str | None = None
        self._decisions_file: str | None = None
        self._prev_features: dict | None = None
        self._scout_tag: int | None = None
        self._scout_waypoints: list[tuple[float, float]] = []
        self._scout_waypoint_index: int = 0
        self._scout_state = ScoutState.IDLE
        self._last_enemy_analysis: dict = {}
        self._last_recommended_counters: dict = {}
        self._cleanup_target_index = 0
        self._scout_metadata = ScoutMetadata(decay_rate=0.05)
        self._worker_scout_tag: int | None = None
        self._worker_scout_waypoint_index: int = 0
        self._worker_scout_active = False
        self._pressure_level: PressureLevel = PressureLevel.NONE
        self._pressure_level_start: float = 0.0

        import os as _os
        _data_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "src", "data", "strategies")
        self._strategy_loader = StrategyLoader(_data_dir)
        self._active_profile = self._strategy_loader.get_default("protoss")
        self._bias_calculator: BiasCalculator | None = None
        self._priority_engine: PriorityEngine | None = None
        self._last_action: Action | None = None
        self._early_game_phase: int = 0
        self._early_game_phase_start: float = 0.0
        self._last_override_source: str | None = None
        self._last_executed_intent: dict | None = None
        self._shadow_profiles: list[tuple[str, StrategyProfile]] = []
        self._shadow_bias_calculators: list[BiasCalculator] = []
        self._shadow_priority_engines: list[PriorityEngine] = []
        self._last_shadow_predictions: list[dict] = []
        self._shadow_last_actions: list[Action | None] = []

        if policy_mode == "ml_shadow":
            if shadow_profiles:
                for name in shadow_profiles:
                    profile = self._strategy_loader.load(f"protoss/{name}.yaml")
                    self._shadow_profiles.append((name, profile))
                    self._shadow_bias_calculators.append(BiasCalculator(profile))
                    self._shadow_priority_engines.append(PriorityEngine(profile))
                self._shadow_last_actions = [None] * len(shadow_profiles)
            else:
                available = self._strategy_loader.load_all("protoss")
                available_names = sorted(p.name for p in available if p.name != getattr(self._active_profile, "name", ""))
                raise ValueError(
                    f"policy_mode 'ml_shadow' requires at least one --shadow-profile. "
                    f"Available profiles: {', '.join(available_names)}"
                )

    async def on_start(self):
        self._decision_state = DecisionState.DEFEND
        self._state_start_time = self.time
        self._surrender_conditions_start = None
        self._enemy_gone_start = None
        self._surrender_fired = False
        self._cleanup_target_index = 0
        self._scout_metadata.clear()
        self._worker_scout_tag = None
        self._worker_scout_waypoint_index = 0
        self._worker_scout_active = False
        self._early_game_phase = 0
        self._early_game_phase_start = 0.0
        self.logger.info("Bot started — race: %s, map: %s", self.race, self.game_info.map_name)

    async def on_step(self, iteration: int):
        self._last_shadow_predictions = []
        if iteration == 0:
            await self.chat_send("En Taro Tassadar! (Protoss macro bot online)")
            self._match_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            reports_root = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "reports",
            )
            self._initialize_report_files(reports_root, self._match_id)

        if not self._surrender_fired and hasattr(self, "state") and self.state.player_result:
            for pr in self.state.player_result:
                if pr.player_id != self.state.common.player_id and pr.result == Result.Defeat.value:
                    self._surrender_fired = True
                    self._decision_state = DecisionState.WON
                    self.logger.info("SC2 engine: enemy defeated — victory")
            if self._decision_state == DecisionState.WON:
                if self._events_file:
                    with open(self._events_file, "a") as f:
                        f.write(json.dumps({
                            "type": "victory",
                            "time": self.time,
                            "step": iteration,
                            "severity": "info",
                            "details": {"source": "player_result"},
                        }) + "\n")
                return

        features = extract_features(self)
        self._last_features = features
        self._last_enemy_analysis = features.get("enemy_army_analysis", {})
        self._last_recommended_counters = features.get("recommended_counters", {})

        self._scout_metadata.apply_decay(self.time)
        for unit_type_name in features.get("enemy_army_composition", {}):
            self._scout_metadata.observe(unit_type_name, self.time)

        features["scout_age"] = self._scout_metadata.to_dict()
        features["building_inference"] = extract_building_inference(self)
        features["eco_inference"] = extract_eco_inference(features)

        if self._features_file:
            with open(self._features_file, "a") as f:
                f.write(json.dumps(features) + "\n")

        events = detect_events(self, features, self._prev_features, iteration)
        self._prev_features = features
        self._enemy_push_active = any(e.type == "enemy_push" for e in events)

        features["enemy_push_active"] = self._enemy_push_active
        self._pressure_level, self._pressure_level_start = assess_pressure(
            features, self.time, self._pressure_level, self._pressure_level_start
        )

        enemy_race_name = self.enemy_race.name.title() if hasattr(self, "enemy_race") else None
        time_in_state = self.time - self._state_start_time

        if self._decision_state != DecisionState.ATTACK:
            game_time = features.get("game_time_seconds", 0)
            threshold = SURRENDER_FOG_ARMY_VALUE_RATIO if self.fog_enabled else SURRENDER_ARMY_VALUE_RATIO
            ratio = features.get("army_value_ratio", 0.0)
            wcount = features.get("worker_count", 0)
            cond_met = (
                game_time >= SURRENDER_MIN_TIME
                and ratio < threshold
                and wcount < SURRENDER_WORKER_MIN
            )
            if cond_met:
                if self._surrender_conditions_start is None:
                    self._surrender_conditions_start = self.time
            else:
                self._surrender_conditions_start = None

        enemy_visible = features.get("enemy_visible_units", 0) + features.get("enemy_visible_structures", 0)
        if enemy_visible == 0 and features.get("game_time_seconds", 0) >= VICTORY_MIN_TIME:
            if self._enemy_gone_start is None:
                self._enemy_gone_start = self.time
        else:
            self._enemy_gone_start = None

        enemy_gone_sustained = self.time - self._enemy_gone_start if self._enemy_gone_start is not None else 0.0

        surrender_sustained = self.time - self._surrender_conditions_start if self._surrender_conditions_start is not None else 0.0

        decision = evaluate_decision(
            features,
            self._decision_state,
            enemy_race_name,
            fog_enabled=self.fog_enabled,
            surrender_enabled=self.surrender_enabled,
            time_in_state=time_in_state,
            surrender_sustained=surrender_sustained,
            enemy_gone_sustained=enemy_gone_sustained,
            enemy_push_active=self._enemy_push_active,
        )

        if decision.state != self._decision_state:
            self.logger.info(
                "decision: %s → %s (%s)",
                self._decision_state.name, decision.state.name, decision.reason,
            )
            self._decision_state = decision.state
            self._state_start_time = self.time
            self._surrender_conditions_start = None
            self._enemy_gone_start = None
            if self._decision_state != DecisionState.ATTACK:
                self._cleanup_target_index = 0

        if self._decision_state == DecisionState.WON and not self._surrender_fired:
            self._surrender_fired = True
            self.logger.info("Victory — enemy eliminated, standing by")
            await self.chat_send("gg")

        if self._decision_state in (DecisionState.SURRENDER, DecisionState.WON):
            if self._events_file:
                event_type = "victory" if self._decision_state == DecisionState.WON else "surrender"
                with open(self._events_file, "a") as f:
                    f.write(json.dumps({
                        "type": event_type,
                        "time": features.get("game_time_seconds", 0),
                        "step": iteration,
                        "severity": "info",
                        "details": {
                            "army_value_ratio": features.get("army_value_ratio", 0),
                            "worker_count": features.get("worker_count", 0),
                            "reason": decision.reason,
                        },
                    }) + "\n")
            return

        if self._events_file and events:
            with open(self._events_file, "a") as f:
                for event in events:
                    f.write(json.dumps({
                        "type": event.type,
                        "time": event.time,
                        "step": event.step,
                        "severity": event.severity,
                        "details": event.details,
                    }) + "\n")

        if iteration - self._last_log >= self.log_interval:
            log_features(self.logger, features, iteration)
            self._last_log = iteration

        if self._decision_state not in (DecisionState.SURRENDER, DecisionState.WON):
            if self._bias_calculator is None:
                self._bias_calculator = BiasCalculator(self._active_profile)
                self._priority_engine = PriorityEngine(self._active_profile)

            if self._bias_calculator and self._priority_engine:
                self._bias_calculator.update(features, self._scout_metadata.to_dict())
                self._last_action = self._priority_engine.evaluate(
                    self._bias_calculator.bias_vector,
                    features,
                    own_composition=features.get("our_army_composition", {}),
                    structures=features.get("our_structures", {}),
                    prev_action=self._last_action,
                )

            for i, (name, _) in enumerate(self._shadow_profiles):
                shadow_bias = self._shadow_bias_calculators[i]
                shadow_engine = self._shadow_priority_engines[i]
                scout_dict = self._scout_metadata.to_dict()
                shadow_bias.update(features, scout_dict)
                shadow_action = shadow_engine.evaluate(
                    shadow_bias.bias_vector,
                    features,
                    own_composition=features.get("our_army_composition", {}),
                    structures=features.get("our_structures", {}),
                    prev_action=self._shadow_last_actions[i] if i < len(self._shadow_last_actions) else None,
                )
                self._shadow_last_actions[i] = shadow_action
                self._last_shadow_predictions.append({
                    "profile": name,
                    "recommended_action": self._serialize_action(shadow_action),
                })

        action = self._last_action if self._last_action and self._decision_state not in (DecisionState.SURRENDER, DecisionState.WON) else None

        await self.manage_early_game()
        await self.manage_probes()
        await self.manage_pylons()
        await self.manage_gas()
        await self.manage_expansion()
        await self.manage_tech(action)
        await self.manage_upgrades(action)
        await self.manage_army(action)
        await self.manage_defense()
        await self.manage_scout()
        await self.manage_attack()
        await self.manage_camera()

        if self._decisions_file:
            self._write_decision_record(iteration, features, self._last_action)

    async def on_end(self, game_result):
        result_name = str(game_result).replace("Result.", "").lower()
        self.logger.info("Game ended — result: %s", result_name)

        replay_path = await save_replay(self, result_name)
        if replay_path:
            self.logger.info("Replay saved: %s", replay_path)

        if self._match_id:
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(__file__))
            )
            match_dir = os.path.join(project_root, "reports", self._match_id)
            features = _load_jsonl(self._features_file or "")
            events = _load_jsonl(self._events_file or "")
            bot_info = {
                "map": getattr(self.game_info, "map_name", "unknown"),
                "opponent_race": self.opponent_race,
                "opponent_difficulty": self.opponent_difficulty,
                "opponent_count": self.opponent_count,
                "result": result_name,
                "policy": self._build_policy_metadata(),
            }
            try:
                generate_report(match_dir, self._match_id, features, events, bot_info)
                generate_index(project_root)
                self.logger.info("Reports generated in %s", match_dir)
            except Exception as e:
                self.logger.error("Failed to generate report: %s", e)

    async def _build_if_able(self, unit_type_id) -> bool:
        if not self.can_afford(unit_type_id):
            self.logger.debug("BUILD %s — FAILED: cant afford", unit_type_id.name)
            return False
        if self.already_pending(unit_type_id):
            return False
        worker = self.workers.idle.first if self.workers.idle.amount > 0 else None
        if worker is None:
            self.logger.debug("BUILD %s — FAILED: no worker available", unit_type_id.name)
            return False
        position = await self.find_placement(unit_type_id, self.start_location, placement_step=5)
        if position is None:
            self.logger.debug("BUILD %s — FAILED: placement failed", unit_type_id.name)
            return False
        await self.build(unit_type_id, near=position)
        self.logger.info("BUILD %s — afford:True placement:True worker:%s", unit_type_id.name, worker.tag)
        return True

    def _initialize_report_files(self, reports_root: str, match_id: str) -> None:
        reports_dir = os.path.join(reports_root, match_id)
        os.makedirs(reports_dir, exist_ok=True)
        self._features_file = os.path.join(reports_dir, "features.jsonl")
        self._events_file = os.path.join(reports_dir, "events.jsonl")
        self._decisions_file = os.path.join(reports_dir, "decisions.jsonl")
        open(self._decisions_file, "a").close()

    @staticmethod
    def _serialize_action(action: Action | None) -> dict | None:
        if action is None:
            return None
        return {
            "type": action.type.name,
            "target": action.target,
            "score": action.score,
        }

    def _build_policy_metadata(self) -> dict:
        profile = self.strategy_profile_name or getattr(self._active_profile, "name", "unknown")
        metadata = {
            "mode": self.policy_mode,
            "selected_policy": "heuristic",
            "heuristic_profile": profile or "unknown",
            "model_name": self.model_name,
            "model_version": self.model_version,
            "experiment_id": self.experiment_id,
            "code_version": "unknown",
        }
        if self.policy_mode == "ml_shadow" and self._shadow_profiles:
            metadata["shadow_profiles"] = [name for name, _ in self._shadow_profiles]
        return metadata

    def _gateway_count(self) -> int:
        return (self.structures(UnitTypeId.GATEWAY).amount +
                self.structures(UnitTypeId.WARPGATE).amount)

    def _build_decision_record(self, iteration: int, features: dict, action: Action | None) -> dict:
        bias_vector = {}
        if self._bias_calculator is not None:
            bias_vector = self._bias_calculator.bias_vector

        profile = self.strategy_profile_name or getattr(self._active_profile, "name", "unknown")
        state = getattr(self._decision_state, "name", str(self._decision_state))
        return {
            "time": features.get("game_time_seconds", getattr(self, "time", 0)),
            "step": iteration,
            "policy_mode": self.policy_mode,
            "selected_policy": "heuristic",
            "strategic_state": state,
            "heuristic_profile": profile or "unknown",
            "early_game_phase": self._early_game_phase,
            "pressure_level": self._pressure_level.name,
            "override_source": self._last_override_source or "none",
            "executed_intent": self._last_executed_intent,
            "utility": {
                "recommended_action": self._serialize_action(action),
                "bias_vector": bias_vector,
            },
            "shadow_predictions": self._last_shadow_predictions,
        }

    def _write_decision_record(self, iteration: int, features: dict, action: Action | None) -> None:
        if not self._decisions_file:
            return
        with open(self._decisions_file, "a") as f:
            f.write(json.dumps(self._build_decision_record(iteration, features, action)) + "\n")

    async def manage_early_game(self):
        self._last_override_source = None
        self._last_executed_intent = None

        if self._early_game_phase >= 5:
            return

        EARLY_PHASE_TIMEOUT = 15.0

        if self._early_game_phase_start == 0.0:
            self._early_game_phase_start = self.time

        phase_elapsed = self.time - self._early_game_phase_start
        if phase_elapsed > EARLY_PHASE_TIMEOUT:
            self.logger.warning("EARLY GAME — phase %d TIMEOUT after %.1fs, skipping", self._early_game_phase, phase_elapsed)
            self._early_game_phase += 1
            self._early_game_phase_start = self.time

        if self._early_game_phase == 0:
            if self.supply_left < 4 and self.structures(UnitTypeId.PYLON).amount < 1:
                if not self.already_pending(UnitTypeId.PYLON):
                    self._last_override_source = "early_game_build_order"
                    self._last_executed_intent = {"type": "BUILD_STRUCTURE", "target": "PYLON"}
                    await self._build_if_able(UnitTypeId.PYLON)
                return
            self._early_game_phase = 1
            self._early_game_phase_start = self.time

        if self._early_game_phase == 1:
            if self.structures(UnitTypeId.GATEWAY).amount == 0:
                self._last_override_source = "early_game_build_order"
                self._last_executed_intent = {"type": "BUILD_STRUCTURE", "target": "GATEWAY"}
                if await self._build_if_able(UnitTypeId.GATEWAY):
                    return
                if self.already_pending(UnitTypeId.GATEWAY):
                    return
            self._early_game_phase = 2
            self._early_game_phase_start = self.time

        if self._early_game_phase == 2:
            if self.structures(UnitTypeId.CYBERNETICSCORE).amount == 0:
                self._last_override_source = "early_game_build_order"
                self._last_executed_intent = {"type": "BUILD_STRUCTURE", "target": "CYBERNETICSCORE"}
                if await self._build_if_able(UnitTypeId.CYBERNETICSCORE):
                    return
                if self.already_pending(UnitTypeId.CYBERNETICSCORE):
                    return
            self._early_game_phase = 3
            self._early_game_phase_start = self.time

        if self._early_game_phase == 3:
            if self._pressure_level.value <= PressureLevel.LOW.value and self.townhalls.amount < 2:
                self._last_override_source = "early_game_build_order"
                self._last_executed_intent = {"type": "BUILD_STRUCTURE", "target": "NEXUS"}
                if await self._build_if_able(UnitTypeId.NEXUS):
                    return
                if self.already_pending(UnitTypeId.NEXUS):
                    return
            self._early_game_phase = 4
            self._early_game_phase_start = self.time

        if self._early_game_phase == 4:
            cyber_cores = self.structures(UnitTypeId.CYBERNETICSCORE).ready
            if cyber_cores.amount > 0 and not self.already_pending_upgrade(UpgradeId.WARPGATERESEARCH):
                if self.can_afford(UpgradeId.WARPGATERESEARCH):
                    self._last_override_source = "early_game_build_order"
                    self._last_executed_intent = {"type": "RESEARCH_UPGRADE", "target": "WARPGATERESEARCH"}
                    cyber_cores.first.research(UpgradeId.WARPGATERESEARCH)
                    self._early_game_phase = 5

    async def manage_probes(self):
        nexus_list = self.townhalls.ready
        if not nexus_list:
            return

        features = getattr(self, "_last_features", {})
        bases = features.get("bases", []) if features else []
        undersaturated = [b for b in bases if b.get("status") == "undersaturated"]
        oversaturated = [b for b in bases if b.get("status") == "oversaturated"]

        effective_max = self._compute_dynamic_max_workers(bases)

        if self.workers.amount >= effective_max:
            undersaturated = []

        if self.supply_left >= 1 and self.can_afford(UnitTypeId.PROBE) and undersaturated:
            sorted_undersat = sorted(undersaturated, key=lambda b: b.get("total_saturation", 0))
            for b in sorted_undersat:
                for nexus in self.townhalls.ready:
                    nx, ny = b.get("position", (0, 0))
                    if abs(nexus.position.x - nx) < 1 and abs(nexus.position.y - ny) < 1:
                        if nexus.is_idle:
                            nexus.train(UnitTypeId.PROBE)
                            if nexus.energy >= 50:
                                nexus(AbilityId.EFFECT_CHRONOBOOST, nexus)
                            return

        await self.manage_worker_transfer(bases, oversaturated, undersaturated)

    def _compute_dynamic_max_workers(self, bases: list[dict]) -> int:
        game_time = (
            getattr(self, "_last_features", {}).get("game_time_seconds", 0)
            if hasattr(self, "_last_features") else 0
        )
        if game_time <= 900:
            return self.MAX_WORKERS
        dynamic = int(sum(b.get("ideal_mineral_workers", 0) + b.get("ideal_gas_workers", 0) for b in bases) * 1.1)
        return min(self.MAX_WORKERS, max(dynamic, 1))

    async def manage_worker_transfer(
        self,
        bases: list[dict],
        oversaturated: list[dict],
        undersaturated: list[dict],
    ):
        if not oversaturated or not undersaturated:
            return

        donor_base = oversaturated[0]
        donor_pos = donor_base.get("position", (0, 0))
        target_base = undersaturated[0]
        target_pos = target_base.get("position", (0, 0))

        target_nexus = None
        for nexus in self.townhalls.ready:
            if abs(nexus.position.x - target_pos[0]) < 1 and abs(nexus.position.y - target_pos[1]) < 1:
                target_nexus = nexus
                break
        if not target_nexus:
            return

        donor_nexus = None
        for nexus in self.townhalls.ready:
            if abs(nexus.position.x - donor_pos[0]) < 1 and abs(nexus.position.y - donor_pos[1]) < 1:
                donor_nexus = nexus
                break

        idle_nearby = donor_base.get("idle_workers_nearby", 0)
        excess_mineral = max(0, donor_base.get("actual_mineral_workers", 0) - 16)

        if idle_nearby > 0:
            for worker in self.workers.idle:
                minerals = self.mineral_field.closer_than(BASE_MINERAL_RADIUS, target_nexus.position)
                if minerals:
                    worker.gather(minerals.first)
                return
        elif excess_mineral > 0 and donor_nexus:
            mineral_workers = [
                w for w in self.workers.gathering
                if not any(
                    g.position.distance_to(w.position) < 3
                    for g in self.gas_buildings.closer_than(BASE_MINERAL_RADIUS, donor_nexus.position)
                )
            ]
            if mineral_workers:
                minerals = self.mineral_field.closer_than(BASE_MINERAL_RADIUS, target_nexus.position)
                if minerals:
                    mineral_workers[0].gather(minerals.first)

    def _get_base_saturation(self, nexus):
        features = getattr(self, "_last_features", {})
        bases = features.get("bases", []) if features else []
        for b in bases:
            bx, by = b.get("position", (0, 0))
            if abs(nexus.position.x - bx) < 1 and abs(nexus.position.y - by) < 1:
                ideal = b.get("ideal_mineral_workers", 0) + b.get("ideal_gas_workers", 0)
                current = b.get("current_workers", 0)
                ratio = b.get("total_saturation", 1.0)
                return ideal, current, ratio
        minerals_nearby = self.mineral_field.closer_than(BASE_MINERAL_RADIUS, nexus.position).amount
        gas_nearby = self.gas_buildings.closer_than(BASE_MINERAL_RADIUS, nexus.position).amount
        ideal = minerals_nearby * 2 + gas_nearby * 3
        current = getattr(nexus, "assigned_harvesters", 0)
        if current == 0 and ideal == 0:
            return 0, 0, 1.0
        ratio = current / ideal if ideal > 0 else 1.0
        return ideal, current, ratio

    def _sort_bases_by_saturation(self):
        features = getattr(self, "_last_features", {})
        bases = features.get("bases", []) if features else []
        if bases:
            sorted_bases = sorted(bases, key=lambda b: b.get("total_saturation", 0))
            result = []
            for b in sorted_bases:
                bx, by = b.get("position", (0, 0))
                for nexus in self.townhalls.ready:
                    if abs(nexus.position.x - bx) < 1 and abs(nexus.position.y - by) < 1:
                        result.append(nexus)
                        break
            return result
        fallback = []
        for nexus in self.townhalls.ready:
            _, _, ratio = self._get_base_saturation(nexus)
            fallback.append((nexus, ratio))
        fallback.sort(key=lambda x: x[1])
        return [b[0] for b in fallback]

    async def manage_pylons(self):
        if self.supply_left >= 4:
            return
        if not self.can_afford(UnitTypeId.PYLON):
            return
        if self.already_pending(UnitTypeId.PYLON):
            return

        position = await self.find_placement(UnitTypeId.PYLON, self.start_location, placement_step=5)
        if position:
            await self.build(UnitTypeId.PYLON, near=position)

    async def manage_gas(self):
        if self.structures(UnitTypeId.PYLON).amount == 0:
            return

        if self._gateway_count() == 0 and self.gas_buildings.amount >= 1:
            await self._assign_gas_workers()
            return

        built = False
        for nexus in self.townhalls.ready:
            vespene_geysers = self.vespene_geyser.closer_than(15, nexus.position)
            for geyser in vespene_geysers:
                if self.gas_buildings.filter(
                    lambda g: g.position.distance_to(geyser.position) < 2
                ):
                    continue
                if not self.can_afford(UnitTypeId.ASSIMILATOR):
                    continue
                worker = self.select_build_worker(geyser.position)
                if worker is None:
                    continue
                worker.build_gas(geyser)
                built = True
                break
            if built:
                break

        await self._assign_gas_workers()

    async def _assign_gas_workers(self):
        for assimilator in self.gas_buildings.ready:
            assigned = getattr(assimilator, "assigned_harvesters", 0)
            if assigned >= 3:
                continue
            workers = self.workers.gathering
            idle = self.workers.idle
            candidates = idle + workers
            for _ in range(3 - assigned):
                if not candidates:
                    break
                worker = candidates.closest_to(assimilator.position)
                if worker:
                    worker.gather(assimilator)

    async def manage_expansion(self):
        if self.already_pending(UnitTypeId.NEXUS):
            return

        sat_threshold = pressure_expand_saturation(self._pressure_level)
        bank_threshold = pressure_expand_mineral_bank(self._pressure_level)

        if sat_threshold is None or bank_threshold is None:
            return

        if self.minerals > bank_threshold and self.can_afford(UnitTypeId.NEXUS):
            await self.expand_now(building=UnitTypeId.NEXUS, max_distance=0)
            return

        if not self.can_afford(UnitTypeId.NEXUS):
            return

        for nexus in self.townhalls.ready:
            _, _, ratio = self._get_base_saturation(nexus)
            if ratio < sat_threshold:
                return

        await self.expand_now(building=UnitTypeId.NEXUS, max_distance=0)

    async def manage_tech(self, action: Action | None = None):
        if not self.townhalls.ready:
            return

        if self._gateway_count() == 0:
            if self.time >= 120:
                self.logger.warning("NO GATEWAY at t=%.1f — emergency build", self.time)
                self._last_override_source = "gateway_emergency_fallback"
                self._last_executed_intent = {"type": "BUILD_STRUCTURE", "target": "GATEWAY"}
            await self._build_if_able(UnitTypeId.GATEWAY)
            return

        if self.structures(UnitTypeId.CYBERNETICSCORE).amount == 0:
            self._last_override_source = "tech_prerequisite_fallback"
            self._last_executed_intent = {"type": "BUILD_STRUCTURE", "target": "CYBERNETICSCORE"}
            await self._build_if_able(UnitTypeId.CYBERNETICSCORE)
            return

        counters = self._last_recommended_counters
        top_3 = list(counters.keys())[:3] if counters else []

        _STARGATE_COUNTER_NAMES = {"VOIDRAY", "PHOENIX", "CARRIER", "TEMPEST"}
        _TWILIGHT_COUNTER_NAMES = {"ARCHON"}

        if any(c in _STARGATE_COUNTER_NAMES for c in top_3):
            if self.structures(UnitTypeId.STARGATE).amount == 0:
                self._last_override_source = "counter_driven_tech"
                self._last_executed_intent = {"type": "BUILD_STRUCTURE", "target": "STARGATE"}
                await self._build_if_able(UnitTypeId.STARGATE)
                return

        if any(c in _TWILIGHT_COUNTER_NAMES for c in top_3):
            if self.structures(UnitTypeId.TWILIGHTCOUNCIL).amount == 0:
                self._last_override_source = "counter_driven_tech"
                self._last_executed_intent = {"type": "BUILD_STRUCTURE", "target": "TWILIGHTCOUNCIL"}
                await self._build_if_able(UnitTypeId.TWILIGHTCOUNCIL)
                return

        if self.structures(UnitTypeId.FORGE).amount == 0:
            if self.minerals + self.vespene >= UPGRADE_RESOURCE_THRESHOLD:
                self._last_override_source = "counter_driven_tech"
                self._last_executed_intent = {"type": "BUILD_STRUCTURE", "target": "FORGE"}
                await self._build_if_able(UnitTypeId.FORGE)
                return

        if action is not None and action.type == ActionType.BUILD_STRUCTURE:
            target_name = action.target
            if target_name in ("STARGATE", "ROBOTICSFACILITY", "TWILIGHTCOUNCIL", "FORGE"):
                if hasattr(UnitTypeId, target_name):
                    type_id = getattr(UnitTypeId, target_name)
                    if await self._build_if_able(type_id):
                        return

        cyber_cores = self.structures(UnitTypeId.CYBERNETICSCORE)

        if cyber_cores.ready.amount > 0:
            if self.can_afford(UpgradeId.WARPGATERESEARCH) and not self.already_pending_upgrade(UpgradeId.WARPGATERESEARCH):
                cyber_cores.ready.first.research(UpgradeId.WARPGATERESEARCH)

        gateway_count = self._gateway_count()
        target = (GATEWAY_MINERAL_BASELINE
                  + pressure_gateway_bonus(self._pressure_level)
                  + max(0, self.townhalls.amount - 1) * GATEWAY_PER_BASE)
        if self.minerals > GATEWAY_MINERAL_FLOAT_THRESHOLD:
            target += pressure_gateway_float_extra(self._pressure_level)
        target_gateways = min(target, MAX_GATEWAYS)

        if gateway_count < target_gateways:
            if not self.already_pending(UnitTypeId.GATEWAY):
                await self._build_if_able(UnitTypeId.GATEWAY)

    async def manage_upgrades(self, action: Action | None = None):
        if action is not None and action.type == ActionType.RESEARCH_UPGRADE:
            target_name = action.target
            if target_name in ("WARPGATERESEARCH", "BLINKTECH", "CHARGE"):
                cyber_cores = self.structures(UnitTypeId.CYBERNETICSCORE)
                twilight_councils = self.structures(UnitTypeId.TWILIGHTCOUNCIL)
                if target_name == "WARPGATERESEARCH" and cyber_cores.ready.amount > 0:
                    if self.can_afford(UpgradeId.WARPGATERESEARCH) and not self.already_pending_upgrade(UpgradeId.WARPGATERESEARCH):
                        cyber_cores.ready.first.research(UpgradeId.WARPGATERESEARCH)
                        return
                if twilight_councils.ready.amount > 0:
                    tid = getattr(UpgradeId, target_name, None)
                    if tid and self.can_afford(tid) and not self.already_pending_upgrade(tid):
                        twilight_councils.ready.first.research(tid)
                        return
            if target_name.startswith("PROTOSSGROUND"):
                forges = self.structures(UnitTypeId.FORGE)
                for forge in forges.ready:
                    tid = getattr(UpgradeId, target_name, None)
                    if tid and self.can_afford(tid) and not self.already_pending_upgrade(tid):
                        forge.research(tid)
                        return

        if self.minerals + self.vespene < UPGRADE_RESOURCE_THRESHOLD:
            return

        forges = self.structures(UnitTypeId.FORGE)

        if should_build_forge(self.minerals, self.vespene, has_forge=forges.amount > 0):
            if self.can_afford(UnitTypeId.FORGE) and not self.already_pending(UnitTypeId.FORGE):
                position = await self.find_placement(UnitTypeId.FORGE, self.start_location, placement_step=5)
                if position:
                    await self.build(UnitTypeId.FORGE, near=position)
            return

        pending: set = set()
        for upgrade in UPGRADE_ORDER:
            if self.already_pending_upgrade(upgrade):
                pending.add(upgrade)

        next_upgrade = get_next_upgrade(set(), pending)
        if next_upgrade is not None:
            for forge in forges.ready:
                if self.can_afford(next_upgrade):
                    forge.research(next_upgrade)
                    return

        cyber_cores = self.structures(UnitTypeId.CYBERNETICSCORE)
        twilight_councils = self.structures(UnitTypeId.TWILIGHTCOUNCIL)

        if should_build_twilight(
            has_cyber_core=cyber_cores.ready.amount > 0,
            has_twilight=twilight_councils.amount > 0,
            minerals=self.minerals,
            vespene=self.vespene,
        ):
            if self.can_afford(UnitTypeId.TWILIGHTCOUNCIL) and not self.already_pending(UnitTypeId.TWILIGHTCOUNCIL):
                position = await self.find_placement(UnitTypeId.TWILIGHTCOUNCIL, self.start_location, placement_step=5)
                if position:
                    await self.build(UnitTypeId.TWILIGHTCOUNCIL, near=position)
            return

        if twilight_councils.ready.amount > 0:
            twilight = twilight_councils.ready.first
            tw_upgrade = get_twilight_upgrade(self._last_enemy_analysis)
            if self.can_afford(tw_upgrade) and not self.already_pending_upgrade(tw_upgrade):
                twilight.research(tw_upgrade)

    async def manage_scout(self):
        if self.time < 30:
            probes = self.workers
            if probes.amount == 0:
                return
            if self._scout_tag is None:
                scout = probes.closest_to(self.enemy_start_locations[0])
                self._scout_tag = scout.tag
                self._scout_waypoints = get_scout_waypoints(self.enemy_start_locations)
                self._scout_waypoint_index = 0
                self._scout_state = ScoutState.EXPLORING

        if self._scout_tag is None:
            return

        scout = self.workers.find_by_tag(self._scout_tag)
        if scout is None:
            scout = self.units.find_by_tag(self._scout_tag)
        if scout is None:
            self._scout_state = ScoutState.DEAD
            return

        if self._scout_state == ScoutState.DEAD:
            return

        enemy_nearby = self.enemy_units.closer_than(8, scout.position)
        if should_retreat_scout(scout, enemy_nearby):
            self._scout_state = ScoutState.RETREATING

        if self._scout_state == ScoutState.RETREATING:
            if self.townhalls:
                scout.move(self.townhalls.first.position)
            return

        move_target = compute_next_scout_move(
            scout, self._scout_waypoints, self._scout_waypoint_index
        )
        if move_target is not None:
            scout.move(Point2(move_target))

        await self._manage_worker_scout()

    async def _manage_worker_scout(self):
        features = getattr(self, "_last_features", {})
        bases = features.get("bases", []) if features else []

        total_idle = sum(b.get("idle_workers_nearby", 0) for b in bases)
        has_oversaturated = any(b.get("status") == "oversaturated" for b in bases)
        game_time = self.time

        scout_confidences = [
            v.get("confidence", 1.0)
            for v in self._scout_metadata.to_dict().values()
            if isinstance(v, dict)
        ]
        avg_confidence = sum(scout_confidences) / len(scout_confidences) if scout_confidences else 1.0

        if self._worker_scout_active:
            worker = None
            if self._worker_scout_tag is not None:
                worker = self.workers.find_by_tag(self._worker_scout_tag)
            if worker is None and self._worker_scout_tag is not None:
                worker = self.units.find_by_tag(self._worker_scout_tag)
            if worker is None:
                self._worker_scout_active = False
                self._worker_scout_tag = None
                return

            move_target = compute_next_scout_move(
                worker, self._scout_waypoints, self._worker_scout_waypoint_index
            )
            if move_target is not None:
                worker.move(Point2(move_target))
            else:
                minerals = self.mineral_field.closer_than(BASE_MINERAL_RADIUS, worker.position)
                if minerals:
                    worker.gather(minerals.first)
                self._worker_scout_active = False
                self._worker_scout_tag = None
            return

        if game_time <= 180:
            return
        if avg_confidence >= 0.4:
            return
        if not (total_idle > 0 or has_oversaturated):
            return

        idle_list = self.workers.idle
        worker = None
        if idle_list.amount > 0:
            worker = idle_list.first
        elif has_oversaturated:
            for b in bases:
                if b.get("status") == "oversaturated":
                    bx, by = b.get("position", (0, 0))
                    for nexus in self.townhalls.ready:
                        if abs(nexus.position.x - bx) < 1 and abs(nexus.position.y - by) < 1:
                            mineral_workers = [
                                w for w in self.workers.gathering
                                if not any(
                                    g.position.distance_to(w.position) < 3
                                    for g in self.gas_buildings.closer_than(BASE_MINERAL_RADIUS, nexus.position)
                                )
                            ]
                            if mineral_workers:
                                worker = mineral_workers[0]
                                break
                    if worker is not None:
                        break
        if worker is None:
            return

        self._worker_scout_tag = worker.tag
        self._worker_scout_waypoint_index = 0
        self._worker_scout_active = True
        if self._scout_waypoints:
            worker.move(Point2(self._scout_waypoints[0]))

    async def manage_army(self, action: Action | None = None):
        engine_unit: UnitTypeId | None = None
        if action is not None and action.type == ActionType.BUILD_UNIT:
            target_name = action.target
            if hasattr(UnitTypeId, target_name):
                engine_unit = getattr(UnitTypeId, target_name)

        counters = self._last_recommended_counters
        top_3 = list(counters.keys())[:3] if counters else []

        _GATEWAY_COUNTERS = {"ZEALOT", "STALKER", "ADEPT", "ARCHON"}
        _ROBO_COUNTERS = {"IMMORTAL", "COLOSSUS", "DISRUPTOR"}
        _STARGATE_COUNTERS = {"VOIDRAY", "PHOENIX", "CARRIER", "TEMPEST"}

        _COUNTER_TO_UNIT = {
            "ZEALOT": UnitTypeId.ZEALOT, "STALKER": UnitTypeId.STALKER,
            "ADEPT": UnitTypeId.ADEPT, "ARCHON": UnitTypeId.ARCHON,
            "IMMORTAL": UnitTypeId.IMMORTAL, "COLOSSUS": UnitTypeId.COLOSSUS,
            "DISRUPTOR": UnitTypeId.DISRUPTOR,
            "VOIDRAY": UnitTypeId.VOIDRAY, "PHOENIX": UnitTypeId.PHOENIX,
            "CARRIER": UnitTypeId.CARRIER, "TEMPEST": UnitTypeId.TEMPEST,
        }

        def _best_counter(counter_set, default):
            for c in top_3:
                if c in counter_set and c in _COUNTER_TO_UNIT:
                    return _COUNTER_TO_UNIT[c]
            return default

        if engine_unit is not None:
            gateway_unit = engine_unit
            robo_unit = engine_unit if engine_unit in _COUNTER_TO_UNIT.values() and any(
                k in _ROBO_COUNTERS for k, v in _COUNTER_TO_UNIT.items() if v == engine_unit
            ) else UnitTypeId.IMMORTAL
            sg_unit = engine_unit if engine_unit in _COUNTER_TO_UNIT.values() and any(
                k in _STARGATE_COUNTERS for k, v in _COUNTER_TO_UNIT.items() if v == engine_unit
            ) else UnitTypeId.VOIDRAY
        else:
            gateway_unit = _best_counter(_GATEWAY_COUNTERS, UnitTypeId.STALKER)
            robo_unit = _best_counter(_ROBO_COUNTERS, UnitTypeId.IMMORTAL)
            sg_unit = _best_counter(_STARGATE_COUNTERS, UnitTypeId.VOIDRAY)

        gw_default = UnitTypeId.ZEALOT if gateway_unit == UnitTypeId.STALKER else UnitTypeId.STALKER

        for gateway in self.structures(UnitTypeId.GATEWAY).ready.idle:
            if self.can_afford(gateway_unit) and self.supply_left >= 2:
                gateway.train(gateway_unit)
            elif self.can_afford(gw_default) and self.supply_left >= 2:
                gateway.train(gw_default)

        for warp_gate in self.structures(UnitTypeId.WARPGATE).ready.idle:
            if self.can_afford(gateway_unit) and self.supply_left >= 2:
                placement = await self.find_placement(
                    gateway_unit, warp_gate.position, placement_step=3
                )
                if placement:
                    warp_gate.warp_in(gateway_unit, placement)
            elif self.can_afford(gw_default) and self.supply_left >= 2:
                placement = await self.find_placement(
                    gw_default, warp_gate.position, placement_step=3
                )
                if placement:
                    warp_gate.warp_in(gw_default, placement)

        for robo in self.structures(UnitTypeId.ROBOTICSFACILITY).ready.idle:
            if self.can_afford(robo_unit) and self.supply_left >= 3:
                robo.train(robo_unit)
            elif self.can_afford(UnitTypeId.IMMORTAL) and self.supply_left >= 3:
                robo.train(UnitTypeId.IMMORTAL)

        for stargate in self.structures(UnitTypeId.STARGATE).ready.idle:
            if self.can_afford(sg_unit) and self.supply_left >= 2:
                stargate.train(sg_unit)
            elif self.can_afford(UnitTypeId.VOIDRAY) and self.supply_left >= 2:
                stargate.train(UnitTypeId.VOIDRAY)

    async def manage_attack(self):
        if self._decision_state != DecisionState.ATTACK:
            return

        army = self._get_army_units()

        if army.amount == 0:
            return

        if army.amount < 4:
            try:
                if self.start_location:
                    for unit in army.idle:
                        unit.move(self.start_location)
            except Exception:
                pass
            return

        if self.enemy_structures.amount > 0:
            for unit in army.idle:
                target = self.enemy_structures.closest_to(unit.position)
                unit.attack(target.position)
            return

        target = self._select_cleanup_target(army)
        if target is None:
            return

        for unit in army.idle:
            unit.attack(target)

    def _get_cleanup_targets(self) -> list[Point2]:
        targets = []
        for location in self.enemy_start_locations:
            targets.append(Point2(location))

        try:
            expansion_locations = self.expansion_locations_list
        except (AssertionError, AttributeError):
            expansion_locations = getattr(self, "_expansion_positions_list", [])

        for location in expansion_locations:
            point = Point2(location)
            if point not in targets:
                targets.append(point)

        return targets

    def _select_cleanup_target(self, army: Units) -> Point2 | None:
        targets = self._get_cleanup_targets()
        if not targets:
            return None

        self._cleanup_target_index %= len(targets)
        target = targets[self._cleanup_target_index]
        closest = army.closest_to(target)
        if closest and closest.position.distance_to(target) <= 8:
            self._cleanup_target_index = (self._cleanup_target_index + 1) % len(targets)
            target = targets[self._cleanup_target_index]
        return target

    async def manage_defense(self):
        if self._decision_state == DecisionState.ATTACK:
            return

        army = self._get_army_units()
        if not army:
            return

        threatened = []
        for nexus in self.townhalls:
            nearby_enemy = self.enemy_units.closer_than(THREAT_RANGE, nexus.position)
            if nearby_enemy:
                score = sum(getattr(u, "supply_cost", 1) for u in nearby_enemy)
                threatened.append((nexus, nearby_enemy, score))

        if not threatened:
            if army.amount >= 8:
                target = getattr(self, "enemy_start_locations", [None])[0]
                if target is None:
                    target = self._compute_defensive_rally()
            else:
                target = self._compute_defensive_rally()
            for unit in army.idle:
                if unit.position.distance_to(target) > 5:
                    unit.move(target)
        else:
            threatened.sort(key=lambda x: x[2], reverse=True)
            nexus, enemies, _ = threatened[0]

            for unit in army.idle:
                dist = unit.position.distance_to(nexus.position)
                if dist > ENGAGE_RANGE:
                    unit.move(nexus.position)
                else:
                    target_unit = enemies.closest_to(unit.position)
                    if target_unit:
                        unit.attack(target_unit)

        for unit in army:
            nearby_enemy = self.enemy_units.closer_than(ENGAGE_RANGE, unit.position)
            if not nearby_enemy:
                continue
            hp_ratio = unit.health / max(unit.health_max, 1)
            if hp_ratio < 0.3 and unit.shield == 0:
                nearest_nexus = self.townhalls.closest_to(unit.position)
                unit.move(nearest_nexus.position)
                continue
            if unit.type_id == UnitTypeId.STALKER:
                for enemy in nearby_enemy:
                    if enemy.ground_range < 2:
                        away = unit.position.towards(enemy.position, -3)
                        unit.move(away)
                        break

    def _compute_defensive_rally(self):
        if len(self.townhalls) >= 2:
            main_pos = self.townhalls.first.position
            nat_pos = self.townhalls[1].position
            return main_pos.towards(nat_pos, main_pos.distance_to(nat_pos) / 2)
        if self.main_base_ramp:
            return self.main_base_ramp.top_center
        return self.start_location

    def _get_army_units(self):
        return self.units.exclude_type(
            [UnitTypeId.PROBE, UnitTypeId.OBSERVER, UnitTypeId.OVERLORD, UnitTypeId.OVERSEER]
        )

    def _determine_camera_mode(self, army, enemy_push_detected: bool) -> CameraMode:
        if self._decision_state == DecisionState.ATTACK and army:
            return CameraMode.ENGAGE
        if enemy_push_detected and self.enemy_units:
            return CameraMode.DEFEND
        if self.supply_used < 30 and army.amount == 0:
            return CameraMode.SCOUT
        if army:
            return CameraMode.ARMY
        return CameraMode.SCOUT

    async def manage_camera(self):
        army = self._get_army_units()
        enemy_push_detected = getattr(self, "_enemy_push_active", False)
        mode = self._determine_camera_mode(army, enemy_push_detected)

        if mode == CameraMode.ENGAGE:
            await self.client.move_camera(army)
        elif mode == CameraMode.DEFEND:
            await self.client.move_camera(self.enemy_units)
        elif mode == CameraMode.SCOUT:
            probes = self.workers
            if probes:
                await self.client.move_camera(probes.first)
            elif self.townhalls:
                await self.client.move_camera(self.townhalls.first)
        elif mode == CameraMode.ARMY:
            await self.client.move_camera(army)
        else:
            if self.townhalls:
                await self.client.move_camera(self.townhalls.first)


def _load_jsonl(path: str) -> list[dict]:
    rows = []
    if path and os.path.isfile(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows
