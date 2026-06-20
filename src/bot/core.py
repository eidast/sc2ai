from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2

from src.ml.observation import extract_features
from src.utils.logger import setup_logger, log_features
from src.utils.replay import save_replay


class MyBot(BotAI):
    MAX_WORKERS = 70
    ATTACK_SUPPLY = 200

    def __init__(self, log_interval: int = 22):
        super().__init__()
        self.attack_triggered = False
        self.logger = setup_logger()
        self.log_interval = log_interval
        self._last_log = 0

    async def on_start(self):
        self.attack_triggered = False
        self.logger.info("Bot started — race: %s, map: %s", self.race, self.game_info.map_name)

    async def on_step(self, iteration: int):
        if iteration == 0:
            await self.chat_send("En Taro Tassadar! (Protoss macro bot online)")

        features = extract_features(self)

        if iteration - self._last_log >= self.log_interval:
            log_features(self.logger, features, iteration)
            self._last_log = iteration

        await self.manage_probes()
        await self.manage_pylons()
        await self.manage_gas()
        await self.manage_expansion()
        await self.manage_tech()
        await self.manage_army()
        await self.manage_attack()
        await self.manage_camera()

    async def on_end(self, game_result):
        result_name = str(game_result).replace("Result.", "").lower()
        self.logger.info("Game ended — result: %s", result_name)
        replay_path = await save_replay(self, result_name)
        if replay_path:
            self.logger.info("Replay saved: %s", replay_path)

    async def manage_probes(self):
        nexus_list = self.townhalls.ready
        if not nexus_list:
            return

        for nexus in nexus_list:
            if (
                nexus.is_idle
                and self.workers.amount < self.MAX_WORKERS
                and self.supply_left >= 1
                and self.can_afford(UnitTypeId.PROBE)
            ):
                nexus.train(UnitTypeId.PROBE)

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

        if self.townhalls.amount >= 2 or self.supply_used < 20:
            return

        location = await self.get_next_expansion()
        if location:
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
        army = self.units.exclude_type(
            [UnitTypeId.PROBE, UnitTypeId.OBSERVER, UnitTypeId.OVERLORD, UnitTypeId.OVERSEER]
        )

        if army.amount == 0:
            return

        if self.supply_used >= self.ATTACK_SUPPLY:
            self.attack_triggered = True

        if self.attack_triggered:
            for unit in army.idle:
                unit.attack(self.enemy_start_locations[0])

    async def manage_camera(self):
        army = self.units.exclude_type(
            [UnitTypeId.PROBE, UnitTypeId.OBSERVER, UnitTypeId.OVERLORD, UnitTypeId.OVERSEER]
        )

        if self.attack_triggered and army:
            await self.client.move_camera(army)
            return

        if self.enemy_units:
            await self.client.move_camera(self.enemy_units)
            return

        if army:
            await self.client.move_camera(army)
            return

        if self.townhalls:
            await self.client.move_camera(self.townhalls.first)
