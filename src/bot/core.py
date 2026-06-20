import json
import os
from datetime import datetime

from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2

from src.bot.strategy import BuildPhase, CameraMode, MAX_SATURATION_RATIO, BASE_MINERAL_RADIUS, THREAT_RANGE, ENGAGE_RANGE

from src.ml.observation import extract_features
from src.ml.events import detect_events
from src.utils.logger import setup_logger, log_features
from src.utils.replay import save_replay
from src.ml.report import generate_report, generate_index


class MyBot(BotAI):
    MAX_WORKERS = 70
    ATTACK_SUPPLY = 200

    def __init__(self, log_interval: int = 22):
        super().__init__()
        self.attack_triggered = False
        self.logger = setup_logger()
        self.log_interval = log_interval
        self._last_log = 0
        self._match_id: str | None = None
        self._features_file: str | None = None
        self._events_file: str | None = None
        self._prev_features: dict | None = None

    async def on_start(self):
        self.attack_triggered = False
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

        if self._features_file:
            with open(self._features_file, "a") as f:
                f.write(json.dumps(features) + "\n")

        events = detect_events(self, features, self._prev_features, iteration)
        self._prev_features = features
        self._enemy_push_active = any(e.type == "enemy_push" for e in events)

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
        await self.manage_army()
        await self.manage_defense()
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
        for nexus in self.townhalls.ready:
            vespene_geysers = self.vespene_geyser.closer_than(15, nexus.position)
            for geyser in vespene_geysers:
                if not self.can_afford(UnitTypeId.ASSIMILATOR):
                    return
                if self.gas_buildings.filter(
                    lambda g: g.position.distance_to(geyser.position) < 2
                ):
                    continue
                worker = self.select_build_worker(geyser.position)
                if worker is None:
                    return
                worker.build_gas(geyser)
                return

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
        target_gateways = 4 if self.townhalls.amount >= 2 else 1

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

    async def manage_army(self):
        for gateway in self.structures(UnitTypeId.GATEWAY).ready.idle:
            if self.can_afford(UnitTypeId.STALKER) and self.supply_left >= 2:
                gateway.train(UnitTypeId.STALKER)
            elif self.can_afford(UnitTypeId.ZEALOT) and self.supply_left >= 2:
                gateway.train(UnitTypeId.ZEALOT)

        for warp_gate in self.structures(UnitTypeId.WARPGATE).ready.idle:
            if self.can_afford(UnitTypeId.STALKER) and self.supply_left >= 2:
                placement = await self.find_placement(
                    UnitTypeId.STALKER, warp_gate.position, placement_step=3
                )
                if placement:
                    warp_gate.warp_in(UnitTypeId.STALKER, placement)
            elif self.can_afford(UnitTypeId.ZEALOT) and self.supply_left >= 2:
                placement = await self.find_placement(
                    UnitTypeId.ZEALOT, warp_gate.position, placement_step=3
                )
                if placement:
                    warp_gate.warp_in(UnitTypeId.ZEALOT, placement)

    async def manage_attack(self):
        army = self._get_army_units()

        if army.amount == 0:
            return

        if self.supply_used >= self.ATTACK_SUPPLY:
            self.attack_triggered = True

        if self.attack_triggered:
            for unit in army.idle:
                unit.attack(self.enemy_start_locations[0])

    async def manage_defense(self):
        if self.attack_triggered:
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
        if self.attack_triggered and army:
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
