from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from src.bot.core import MyBot
from src.strategies.types import Action, ActionType


class FakeStructures:
    def __init__(self, gateways=0, gateways_ready=0, cyber_cores=0, cyber_cores_ready=0):
        self._gateways = gateways
        self._gateways_ready = gateways_ready
        self._cyber_cores = cyber_cores
        self._cyber_cores_ready = cyber_cores_ready

    def _make_ready(self, amt):
        obj = SimpleNamespace(amount=amt, idle=[])
        obj.first = SimpleNamespace()
        obj.first.research = MagicMock()
        return obj

    def __call__(self, unit_type=None):
        if unit_type == UnitTypeId.GATEWAY:
            amt = self._gateways
            rdy = self._gateways_ready
        elif unit_type == UnitTypeId.CYBERNETICSCORE:
            amt = self._cyber_cores
            rdy = self._cyber_cores_ready
        else:
            amt = 0
            rdy = 0
        return SimpleNamespace(
            amount=amt,
            ready=self._make_ready(rdy),
        )


def _make_bot(**overrides):
    bot = MyBot.__new__(MyBot)
    MyBot.__init__(bot)

    bot.supply_left = overrides.get("supply_left", 2)
    bot.minerals = overrides.get("minerals", 200)
    bot.vespene = overrides.get("vespene", 100)
    bot._early_game_phase = overrides.get("early_game_phase", 0)
    bot._early_game_phase_start = overrides.get("early_game_phase_start", 5.0)

    fake_time = overrides.get("time", 10.0)
    time_patcher = patch.object(MyBot, "time", PropertyMock(return_value=fake_time))
    time_patcher.start()

    start_loc = SimpleNamespace(x=50.0, y=50.0)
    start_patcher = patch.object(MyBot, "start_location", PropertyMock(return_value=start_loc))
    start_patcher.start()

    class FakeIdleWorkers:
        amount = overrides.get("idle_workers", 2)
        first = SimpleNamespace(tag=999)

    bot.workers = SimpleNamespace(idle=FakeIdleWorkers(), amount=12)

    class FakeGasBuildings:
        amount = overrides.get("gas_buildings", 0)
        ready = []

        def filter(self, _fn):
            return []

    bot.gas_buildings = FakeGasBuildings()

    bot.townhalls = SimpleNamespace(
        ready=[SimpleNamespace(position=SimpleNamespace(x=50.0, y=50.0))],
        amount=1,
        first=SimpleNamespace(position=SimpleNamespace(x=50.0, y=50.0)),
    )

    bot.structures = FakeStructures(
        gateways=overrides.get("gateways", 0),
        gateways_ready=overrides.get("gateways_ready", 0),
        cyber_cores=overrides.get("cyber_cores", 0),
        cyber_cores_ready=overrides.get("cyber_cores_ready", 0),
    )
    bot.can_afford = MagicMock(return_value=True)
    bot.already_pending = MagicMock(return_value=False)
    bot.already_pending_upgrade = MagicMock(return_value=False)
    bot.find_placement = AsyncMock(return_value=SimpleNamespace(x=55.0, y=55.0))
    bot.build = AsyncMock(return_value=True)
    bot.expand_now = AsyncMock(return_value=True)
    bot._get_base_saturation = MagicMock(return_value=(16, 12, 0.75))
    bot.logger = MagicMock()
    return bot


class TestBuildIfAble:
    async def test_build_if_able_success(self):
        bot = _make_bot()
        result = await bot._build_if_able(UnitTypeId.GATEWAY)
        assert result is True
        bot.build.assert_awaited_once()

    async def test_build_if_able_cant_afford(self):
        bot = _make_bot()
        bot.can_afford.return_value = False
        result = await bot._build_if_able(UnitTypeId.GATEWAY)
        assert result is False
        bot.build.assert_not_awaited()

    async def test_build_if_able_already_pending(self):
        bot = _make_bot()
        bot.already_pending.return_value = True
        result = await bot._build_if_able(UnitTypeId.GATEWAY)
        assert result is False

    async def test_build_if_able_no_idle_worker(self):
        bot = _make_bot(idle_workers=0)
        result = await bot._build_if_able(UnitTypeId.GATEWAY)
        assert result is False
        bot.build.assert_not_awaited()

    async def test_build_if_able_placement_failed(self):
        bot = _make_bot()
        bot.find_placement.return_value = None
        result = await bot._build_if_able(UnitTypeId.GATEWAY)
        assert result is False
        bot.build.assert_not_awaited()


class TestManageEarlyGame:
    async def test_returns_early_when_time_exceeds_90(self):
        bot = _make_bot(time=95.0)
        bot.find_placement.return_value = None
        await bot.manage_early_game()
        bot.build.assert_not_awaited()

    async def test_phase_0_builds_pylon_when_supply_low(self):
        bot = _make_bot(supply_left=2, early_game_phase=0, gateways=0)
        await bot.manage_early_game()
        bot.build.assert_awaited_once()

    async def test_phase_0_skips_pylon_when_supply_ok(self):
        bot = _make_bot(supply_left=6, early_game_phase=0, gateways=0)
        await bot.manage_early_game()
        assert bot._early_game_phase == 1

    async def test_phase_1_builds_gateway_when_none_exists(self):
        bot = _make_bot(early_game_phase=1, gateways=0)
        await bot.manage_early_game()
        bot.build.assert_awaited_once()

    async def test_phase_1_advances_when_gateway_exists(self):
        bot = _make_bot(early_game_phase=1, gateways=1)
        await bot.manage_early_game()
        assert bot._early_game_phase == 2

    async def test_phase_2_builds_cyber_core_when_none_exists(self):
        bot = _make_bot(early_game_phase=2, gateways=1, cyber_cores=0)
        await bot.manage_early_game()
        bot.build.assert_awaited_once()

    async def test_phase_2_advances_when_cyber_core_exists(self):
        bot = _make_bot(early_game_phase=2, gateways=1, cyber_cores=1)
        await bot.manage_early_game()
        assert bot._early_game_phase == 3

    async def test_phase_timeout_skips_to_next(self):
        bot = _make_bot(early_game_phase=1, early_game_phase_start=0.0, time=20.0, gateways=0)
        bot.already_pending.return_value = False
        bot.find_placement.return_value = None
        await bot.manage_early_game()
        assert bot._early_game_phase >= 2

    async def test_phase_3_researches_warp_gate(self):
        bot = _make_bot(early_game_phase=3, gateways=1, cyber_cores=1, cyber_cores_ready=1)
        bot.already_pending_upgrade.return_value = False
        await bot.manage_early_game()
        assert bot._early_game_phase == 4

    async def test_all_phases_complete_returns_without_side_effects(self):
        bot = _make_bot(time=50.0, early_game_phase=4)
        bot.build.reset_mock()
        bot.already_pending_upgrade.reset_mock()
        await bot.manage_early_game()
        bot.build.assert_not_awaited()


class TestManageTechRework:
    async def test_gateway_built_first_when_missing(self):
        bot = _make_bot(gateways=0)
        action = Action(type=ActionType.BUILD_STRUCTURE, target="FORGE", score=0.9)
        await bot.manage_tech(action)
        bot.build.assert_awaited_once()

    async def test_gateway_emergency_fallback_at_120s(self):
        bot = _make_bot(time=125.0, gateways=0)
        action = Action(type=ActionType.BUILD_STRUCTURE, target="FORGE", score=0.9)
        await bot.manage_tech(action)
        bot.build.assert_awaited_once()

    async def test_cyber_core_built_after_gateway(self):
        bot = _make_bot(gateways=1, gateways_ready=1, cyber_cores=0)
        action = Action(type=ActionType.BUILD_STRUCTURE, target="FORGE", score=0.9)
        await bot.manage_tech(action)
        bot.build.assert_awaited_once()

    async def test_action_based_tech_after_gateway_and_core(self):
        bot = _make_bot(gateways=1, gateways_ready=1, cyber_cores=1, cyber_cores_ready=1)
        action = Action(type=ActionType.BUILD_STRUCTURE, target="ROBOTICSFACILITY", score=0.9)
        await bot.manage_tech(action)
        bot.build.assert_awaited_once()


class TestManageGasGatewayGuard:
    async def test_no_second_assimilator_without_gateway(self):
        bot = _make_bot(gateways=0, gas_buildings=1)

        class FakeGeyser:
            position = SimpleNamespace(x=52.0, y=52.0)

        bot.vespene_geyser = SimpleNamespace()
        bot.vespene_geyser.closer_than = lambda _r, _p: [FakeGeyser()]
        bot.select_build_worker = MagicMock(return_value=SimpleNamespace(tag=1))
        bot._assign_gas_workers = AsyncMock()

        await bot.manage_gas()
        bot.select_build_worker.assert_not_called()

    async def test_assimilator_built_when_gateway_exists(self):
        bot = _make_bot(gateways=1, gas_buildings=0)

        class FakeGeyser:
            position = SimpleNamespace(x=52.0, y=52.0)

        bot.vespene_geyser = SimpleNamespace()
        bot.vespene_geyser.closer_than = lambda _r, _p: [FakeGeyser()]
        fake_worker = SimpleNamespace(tag=1)
        fake_worker.build_gas = MagicMock()
        bot.select_build_worker = MagicMock(return_value=fake_worker)
        bot._assign_gas_workers = AsyncMock()

        await bot.manage_gas()
        fake_worker.build_gas.assert_called_once()


class TestManageExpansionMineralBanking:
    async def test_mineral_banking_triggers_expansion(self):
        bot = _make_bot(minerals=500)
        bot.already_pending.return_value = False
        bot.can_afford.return_value = True
        await bot.manage_expansion()
        bot.expand_now.assert_awaited_once()

    async def test_no_expansion_when_already_pending(self):
        bot = _make_bot(minerals=500)
        bot.already_pending.return_value = True
        bot.can_afford.return_value = True
        bot.expand_now.reset_mock()
        await bot.manage_expansion()
        bot.expand_now.assert_not_awaited()

    async def test_no_expansion_below_400_minerals(self):
        bot = _make_bot(minerals=300)
        bot.already_pending.return_value = False
        bot.can_afford.return_value = False
        bot.expand_now.reset_mock()
        await bot.manage_expansion()
        bot.expand_now.assert_not_awaited()
