import json
import os
from datetime import datetime

from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2

from src.bot.strategy import BuildPhase, CameraMode, MAX_SATURATION_RATIO, BASE_MINERAL_RADIUS, THREAT_RANGE, ENGAGE_RANGE, GATEWAY_MINERAL_BASELINE, GATEWAY_PER_BASE, GATEWAY_MINERAL_FLOAT_THRESHOLD, GATEWAY_MINERAL_FLOAT_EXTRA, MAX_GATEWAYS, FORGE_MINERAL_THRESHOLD

from src.ml.observation import extract_features
from src.ml.events import detect_events
from src.utils.logger import setup_logger, log_features
from src.utils.replay import save_replay
from src.ml.report import generate_report, generate_index

from src.bot.scout import (
    ScoutState, get_scout_waypoints, should_retreat_scout,
    compute_next_scout_move, update_scout_waypoints,
)
from src.bot.upgrades import (
    UPGRADE_ORDER, get_next_upgrade, should_build_forge,
    should_build_twilight, get_twilight_upgrade,
)
from src.bot.decision import evaluate_decision, DecisionState, SURRENDER_MIN_TIME, SURRENDER_ARMY_VALUE_RATIO, SURRENDER_WORKER_MIN, SURRENDER_FOG_ARMY_VALUE_RATIO, VICTORY_MIN_TIME, VICTORY_ENEMY_GONE_SECONDS, VICTORY_MIN_ARMY


class MyBot(BotAI):
    MAX_WORKERS = 70
    ATTACK_SUPPLY = 200

    def __init__(self, log_interval: int = 22, surrender_enabled: bool = False, fog_enabled: bool = False):
        super().__init__()
        self.logger = setup_logger()
        self.log_interval = log_interval
        self.surrender_enabled = surrender_enabled
        self.fog_enabled = fog_enabled
        self._decision_state = DecisionState.DEFEND
        self._state_start_time: float = 0.0
        self._surrender_conditions_start: float | None = None
        self._enemy_gone_start: float | None = None
        self._surrender_fired = False
        self._last_log = 0
        self._match_id: str | None = None
        self._features_file: str | None = None
        self._events_file: str | None = None
        self._prev_features: dict | None = None
        self._scout_tag: int | None = None
        self._scout_waypoints: list[tuple[float, float]] = []
        self._scout_waypoint_index: int = 0
        self._scout_state = ScoutState.IDLE
        self._last_enemy_analysis: dict = {}
        self._last_recommended_counters: dict = {}

    async def on_start(self):
        self._decision_state = DecisionState.DEFEND
        self._state_start_time = self.time
        self._surrender_conditions_start = None
        self._enemy_gone_start = None
        self._surrender_fired = False
        self.logger.info("Bot started — race: %s, map: %s", self.race, self.game_info.map_name)

    async def on_step(self, iteration: int):
        if iteration == 0:
            await self.chat_send("En Taro Tassadar! (Protoss macro bot online)")
            self._match_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            reports_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "reports",
                self._match_id,
            )
            os.makedirs(reports_dir, exist_ok=True)
            self._features_file = os.path.join(reports_dir, "features.jsonl")
            self._events_file = os.path.join(reports_dir, "events.jsonl")

        features = extract_features(self)
        self._last_enemy_analysis = features.get("enemy_army_analysis", {})
        self._last_recommended_counters = features.get("recommended_counters", {})

        if self._features_file:
            with open(self._features_file, "a") as f:
                f.write(json.dumps(features) + "\n")

        events = detect_events(self, features, self._prev_features, iteration)
        self._prev_features = features
        self._enemy_push_active = any(e.type == "enemy_push" for e in events)

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

        enemy_visible = features.get("enemy_visible_units", 0)
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

        await self.manage_probes()
        await self.manage_pylons()
        await self.manage_gas()
        await self.manage_expansion()
        await self.manage_tech()
        await self.manage_upgrades()
        await self.manage_army()
        await self.manage_defense()
        await self.manage_scout()
        await self.manage_attack()
        await self.manage_camera()

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
                "opponent_race": self.enemy_race.name if hasattr(self, "enemy_race") else "unknown",
                "opponent_difficulty": "Medium",
                "result": result_name,
            }
            try:
                generate_report(match_dir, self._match_id, features, events, bot_info)
                generate_index(project_root)
                self.logger.info("Reports generated in %s", match_dir)
            except Exception as e:
                self.logger.error("Failed to generate report: %s", e)

    async def manage_probes(self):
        nexus_list = self.townhalls.ready
        if not nexus_list:
            return

        if self.workers.amount >= self.MAX_WORKERS:
            return

        if self.supply_left < 1:
            return

        if not self.can_afford(UnitTypeId.PROBE):
            return

        sorted_bases = self._sort_bases_by_saturation()
        for nexus in sorted_bases:
            ideal, current, ratio = self._get_base_saturation(nexus)
            if ratio < MAX_SATURATION_RATIO and nexus.is_idle:
                nexus.train(UnitTypeId.PROBE)
                return

    def _get_base_saturation(self, nexus):
        minerals_nearby = self.mineral_field.closer_than(BASE_MINERAL_RADIUS, nexus.position).amount
        gas_nearby = self.gas_buildings.closer_than(BASE_MINERAL_RADIUS, nexus.position).amount
        ideal = minerals_nearby * 2 + gas_nearby * 3
        current = getattr(nexus, "assigned_harvesters", 0)
        if current == 0 and ideal == 0:
            return 0, 0, 1.0
        ratio = current / ideal if ideal > 0 else 1.0
        return ideal, current, ratio

    def _sort_bases_by_saturation(self):
        bases = []
        for nexus in self.townhalls.ready:
            _, _, ratio = self._get_base_saturation(nexus)
            bases.append((nexus, ratio))
        bases.sort(key=lambda x: x[1])
        return [b[0] for b in bases]

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
        if not self.can_afford(UnitTypeId.NEXUS):
            return
        if self.already_pending(UnitTypeId.NEXUS):
            return

        for nexus in self.townhalls.ready:
            _, _, ratio = self._get_base_saturation(nexus)
            if ratio < MAX_SATURATION_RATIO:
                return

        await self.expand_now(building=UnitTypeId.NEXUS, max_distance=0)

    async def manage_tech(self):
        if not self.townhalls.ready:
            return

        cyber_cores = self.structures(UnitTypeId.CYBERNETICSCORE)
        gateways = self.structures(UnitTypeId.GATEWAY)
        target = GATEWAY_MINERAL_BASELINE + max(0, self.townhalls.amount - 1) * GATEWAY_PER_BASE
        if self.minerals > GATEWAY_MINERAL_FLOAT_THRESHOLD:
            target += GATEWAY_MINERAL_FLOAT_EXTRA
        target_gateways = min(target, MAX_GATEWAYS)

        if gateways.amount == 0:
            if self.can_afford(UnitTypeId.GATEWAY) and not self.already_pending(UnitTypeId.GATEWAY):
                position = await self.find_placement(UnitTypeId.GATEWAY, self.start_location, placement_step=5)
                if position:
                    await self.build(UnitTypeId.GATEWAY, near=position)
            return

        if cyber_cores.amount == 0 and gateways.ready.amount > 0:
            if self.can_afford(UnitTypeId.CYBERNETICSCORE) and not self.already_pending(UnitTypeId.CYBERNETICSCORE):
                position = await self.find_placement(UnitTypeId.CYBERNETICSCORE, self.start_location, placement_step=5)
                if position:
                    await self.build(UnitTypeId.CYBERNETICSCORE, near=position)
            return

        if cyber_cores.ready.amount > 0:
            warp_gate_ability = self.can_afford(UpgradeId.WARPGATERESEARCH)
            if warp_gate_ability and not self.already_pending_upgrade(UpgradeId.WARPGATERESEARCH):
                cyber_cores.ready.first.research(UpgradeId.WARPGATERESEARCH)

        if gateways.amount < target_gateways and self.can_afford(UnitTypeId.GATEWAY):
            if not self.already_pending(UnitTypeId.GATEWAY):
                position = await self.find_placement(UnitTypeId.GATEWAY, self.start_location, placement_step=5)
                if position:
                    await self.build(UnitTypeId.GATEWAY, near=position)

    async def manage_upgrades(self):
        if self.minerals < FORGE_MINERAL_THRESHOLD:
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

    async def manage_army(self):
        counters = self._last_recommended_counters

        primary_unit = UnitTypeId.STALKER
        secondary_unit = UnitTypeId.ZEALOT

        if counters:
            top_counter = next(iter(counters), None)
            if top_counter == "IMMORTAL":
                primary_unit = UnitTypeId.IMMORTAL
                secondary_unit = UnitTypeId.STALKER
            elif top_counter == "ZEALOT":
                primary_unit = UnitTypeId.ZEALOT
                secondary_unit = UnitTypeId.STALKER

        for gateway in self.structures(UnitTypeId.GATEWAY).ready.idle:
            if self.can_afford(primary_unit) and self.supply_left >= 2:
                gateway.train(primary_unit)
            elif self.can_afford(secondary_unit) and self.supply_left >= 2:
                gateway.train(secondary_unit)

        for warp_gate in self.structures(UnitTypeId.WARPGATE).ready.idle:
            if self.can_afford(primary_unit) and self.supply_left >= 2:
                placement = await self.find_placement(
                    primary_unit, warp_gate.position, placement_step=3
                )
                if placement:
                    warp_gate.warp_in(primary_unit, placement)
            elif self.can_afford(secondary_unit) and self.supply_left >= 2:
                placement = await self.find_placement(
                    secondary_unit, warp_gate.position, placement_step=3
                )
                if placement:
                    warp_gate.warp_in(secondary_unit, placement)

    async def manage_attack(self):
        if self._decision_state != DecisionState.ATTACK:
            return

        army = self._get_army_units()

        if army.amount == 0:
            return

        for unit in army.idle:
            unit.attack(self.enemy_start_locations[0])

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
            rally = self._compute_defensive_rally()
            for unit in army.idle:
                if unit.position.distance_to(rally) > 5:
                    unit.move(rally)
            return

        threatened.sort(key=lambda x: x[2], reverse=True)
        nexus, enemies, _ = threatened[0]

        for unit in army.idle:
            dist = unit.position.distance_to(nexus.position)
            if dist > ENGAGE_RANGE:
                unit.move(nexus.position)
            else:
                target = enemies.closest_to(unit.position)
                if target:
                    unit.attack(target)

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
