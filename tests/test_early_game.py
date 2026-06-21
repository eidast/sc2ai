import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from src.bot.core import MyBot
from src.bot.pressure import PressureLevel
from src.strategies.types import Action, ActionType


class FakeStructures:
    def __init__(self, gateways=0, gateways_ready=0, warpgates=0, cyber_cores=0, cyber_cores_ready=0, pylons=0):
        self._gateways = gateways
        self._gateways_ready = gateways_ready
        self._warpgates = warpgates
        self._cyber_cores = cyber_cores
        self._cyber_cores_ready = cyber_cores_ready
        self._pylons = pylons

    def _make_ready(self, amt):
        obj = SimpleNamespace(amount=amt, idle=[])
        obj.first = SimpleNamespace()
        obj.first.research = MagicMock()
        return obj

    def __call__(self, unit_type=None):
        if unit_type == UnitTypeId.GATEWAY:
            amt = self._gateways
            rdy = self._gateways_ready
        elif unit_type == UnitTypeId.WARPGATE:
            amt = self._warpgates
            rdy = 0
        elif unit_type == UnitTypeId.CYBERNETICSCORE:
            amt = self._cyber_cores
            rdy = self._cyber_cores_ready
        elif unit_type == UnitTypeId.PYLON:
            amt = self._pylons
            rdy = 0
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
        warpgates=overrides.get("warpgates", 0),
        cyber_cores=overrides.get("cyber_cores", 0),
        cyber_cores_ready=overrides.get("cyber_cores_ready", 0),
        pylons=overrides.get("pylons", 1),
    )
    bot.can_afford = MagicMock(return_value=True)
    bot._pressure_level = overrides.get("pressure_level", PressureLevel.NONE)
    bot._pressure_level_start = overrides.get("pressure_level_start", 0.0)
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
        bot = _make_bot(supply_left=2, early_game_phase=0, gateways=0, pylons=0)
        await bot.manage_early_game()
        bot.build.assert_awaited_once()
        assert bot._last_override_source == "early_game_build_order"
        assert bot._last_executed_intent == {"type": "BUILD_STRUCTURE", "target": "PYLON"}

    async def test_phase_0_skips_pylon_when_supply_ok(self):
        bot = _make_bot(supply_left=6, early_game_phase=0, gateways=0)
        await bot.manage_early_game()
        assert bot._early_game_phase == 1

    async def test_phase_1_builds_gateway_when_none_exists(self):
        bot = _make_bot(early_game_phase=1, gateways=0)
        await bot.manage_early_game()
        bot.build.assert_awaited_once()
        assert bot._last_override_source == "early_game_build_order"
        assert bot._last_executed_intent == {"type": "BUILD_STRUCTURE", "target": "GATEWAY"}

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

    async def test_phase_4_researches_warp_gate(self):
        bot = _make_bot(early_game_phase=4, gateways=1, cyber_cores=1, cyber_cores_ready=1)
        bot.already_pending_upgrade.return_value = False
        await bot.manage_early_game()
        assert bot._early_game_phase == 5
        assert bot._last_override_source == "early_game_build_order"
        assert bot._last_executed_intent == {"type": "RESEARCH_UPGRADE", "target": "WARPGATERESEARCH"}

    def test_decision_record_includes_early_game_context(self):
        bot = _make_bot(early_game_phase=2)
        bot.policy_mode = "ml_shadow"
        bot.strategy_profile_name = None
        bot._active_profile = SimpleNamespace(name="standard_macro")
        bot._decision_state = SimpleNamespace(name="DEFEND")
        bot._last_override_source = "early_game_build_order"
        bot._last_executed_intent = {"type": "BUILD_STRUCTURE", "target": "CYBERNETICSCORE"}
        action = Action(type=ActionType.BUILD_STRUCTURE, target="FORGE", score=0.42)

        record = bot._build_decision_record(iteration=7, features={"game_time_seconds": 12}, action=action)

        assert record["policy_mode"] == "ml_shadow"
        assert record["selected_policy"] == "heuristic"
        assert record["strategic_state"] == "DEFEND"
        assert record["early_game_phase"] == 2
        assert record["override_source"] == "early_game_build_order"
        assert record["executed_intent"] == {"type": "BUILD_STRUCTURE", "target": "CYBERNETICSCORE"}
        assert record["utility"]["recommended_action"] == {"type": "BUILD_STRUCTURE", "target": "FORGE", "score": 0.42}

    def test_decision_record_handles_missing_optional_context(self):
        bot = _make_bot(early_game_phase=4)
        bot.policy_mode = "ml_shadow"
        bot.strategy_profile_name = "standard_macro"
        bot._decision_state = SimpleNamespace(name="DEFEND")
        bot._bias_calculator = None

        record = bot._build_decision_record(iteration=8, features={"game_time_seconds": 30}, action=None)

        assert record["override_source"] == "none"
        assert record["executed_intent"] is None
        assert record["utility"]["recommended_action"] is None
        assert record["utility"]["bias_vector"] == {}
        assert record["shadow_predictions"] == []

    def test_decision_record_includes_available_shadow_prediction(self):
        bot = _make_bot(early_game_phase=4)
        bot.policy_mode = "ml_shadow"
        bot.strategy_profile_name = "standard_macro"
        bot._decision_state = SimpleNamespace(name="DEFEND")
        bot._last_shadow_predictions = [
            {
                "profile": "stargate_open",
                "recommended_action": {
                    "type": "BUILD_STRUCTURE",
                    "target": "STARGATE",
                    "score": 0.72,
                },
            },
        ]

        record = bot._build_decision_record(iteration=8, features={"game_time_seconds": 30}, action=None)

        assert record["shadow_predictions"] == [
            {
                "profile": "stargate_open",
                "recommended_action": {
                    "type": "BUILD_STRUCTURE",
                    "target": "STARGATE",
                    "score": 0.72,
                },
            },
        ]

    def test_write_decision_record_writes_valid_jsonl(self, tmp_path):
        bot = _make_bot(early_game_phase=4)
        bot.policy_mode = "heuristic"
        bot.strategy_profile_name = "standard_macro"
        bot._decision_state = SimpleNamespace(name="DEFEND")
        bot._decisions_file = str(tmp_path / "decisions.jsonl")

        bot._write_decision_record(9, {"game_time_seconds": 44}, None)

        lines = (tmp_path / "decisions.jsonl").read_text().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["step"] == 9
        assert "minerals" not in record
        assert record["utility"]["recommended_action"] is None

    def test_write_decision_record_persists_shadow_prediction(self, tmp_path):
        bot = _make_bot(early_game_phase=4)
        bot.policy_mode = "ml_shadow"
        bot.strategy_profile_name = "standard_macro"
        bot._decision_state = SimpleNamespace(name="DEFEND")
        bot._decisions_file = str(tmp_path / "decisions.jsonl")
        bot._last_shadow_predictions = [
            {"profile": "stargate_open", "recommended_action": {"type": "BUILD_UNIT", "target": "STALKER", "score": 0.85}},
        ]

        bot._write_decision_record(10, {"game_time_seconds": 50}, None)

        record = json.loads((tmp_path / "decisions.jsonl").read_text())
        assert record["policy_mode"] == "ml_shadow"
        assert record["selected_policy"] == "heuristic"
        assert record["shadow_predictions"] == [
            {"profile": "stargate_open", "recommended_action": {"type": "BUILD_UNIT", "target": "STALKER", "score": 0.85}},
        ]

    async def test_all_phases_complete_returns_without_side_effects(self):
        bot = _make_bot(time=50.0, early_game_phase=4)
        bot.build.reset_mock()
        bot.already_pending_upgrade.reset_mock()
        await bot.manage_early_game()
        bot.build.assert_not_awaited()

    async def test_fast_expand_phase_3_builds_nexus_when_no_pressure(self):
        bot = _make_bot(time=60.0, early_game_phase=3, early_game_phase_start=55.0, pressure_level=PressureLevel.NONE)
        bot.build.reset_mock()
        await bot.manage_early_game()
        bot.build.assert_awaited_once()

    async def test_fast_expand_skipped_under_medium_pressure(self):
        bot = _make_bot(time=60.0, early_game_phase=3, early_game_phase_start=55.0, pressure_level=PressureLevel.MEDIUM)
        bot.build.reset_mock()
        await bot.manage_early_game()
        bot.build.assert_not_awaited()
        assert bot._early_game_phase == 4


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


class TestShadowEngineIntegration:
    def test_shadow_engines_produce_predictions(self):
        bot = _make_bot()
        bot.policy_mode = "ml_shadow"
        bot._shadow_profiles = [("stargate_open", SimpleNamespace(name="stargate_open"))]
        bot._last_shadow_predictions = []

        mock_bias = MagicMock()
        mock_bias.bias_vector = {"stargate_units": 0.8}
        mock_bias.update = MagicMock(return_value={"stargate_units": 0.8})

        mock_engine = MagicMock()
        shadow_action = Action(type=ActionType.BUILD_UNIT, target="VOIDRAY", score=0.92)
        mock_engine.evaluate = MagicMock(return_value=shadow_action)

        bot._shadow_bias_calculators = [mock_bias]
        bot._shadow_priority_engines = [mock_engine]
        bot._scout_metadata = MagicMock()
        bot._scout_metadata.to_dict = MagicMock(return_value={"marine": {"confidence": 0.5}})

        bot._last_shadow_predictions = []
        for i, (name, _) in enumerate(bot._shadow_profiles):
            shadow_bias = bot._shadow_bias_calculators[i]
            shadow_engine = bot._shadow_priority_engines[i]
            scout_dict = bot._scout_metadata.to_dict()
            shadow_bias.update({}, scout_dict)
            shadow_action = shadow_engine.evaluate(
                shadow_bias.bias_vector,
                {},
                own_composition={},
                structures={},
            )
            bot._last_shadow_predictions.append({
                "profile": name,
                "recommended_action": bot._serialize_action(shadow_action),
            })

        assert len(bot._last_shadow_predictions) == 1
        pred = bot._last_shadow_predictions[0]
        assert pred["profile"] == "stargate_open"
        assert pred["recommended_action"] == {
            "type": "BUILD_UNIT",
            "target": "VOIDRAY",
            "score": 0.92,
        }
