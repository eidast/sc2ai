"""Integration tests: verify engine produces actions and FSM overrides work."""

import pytest
from src.strategies.types import Action, ActionType, StrategyProfile, MetaParams, ScoutingAdjustment, FormulaEntry
from src.strategies.bias_calculator import BiasCalculator
from src.strategies.priority_engine import PriorityEngine
from src.strategies.loader import StrategyLoader
from pathlib import Path


_DATA_DIR = Path(__file__).parent.parent / "src" / "data" / "strategies"


class TestEngineIntegration:
    def test_engine_produces_action_for_normal_game(self):
        profile = StrategyLoader(_DATA_DIR).get_default("protoss")
        calc = BiasCalculator(profile)
        engine = PriorityEngine(profile)

        features = {
            "minerals": 500, "vespene": 300,
            "supply_left": 5, "supply_used": 25, "supply_cap": 30,
            "worker_count": 20, "army_count": 0,
            "game_time_seconds": 120, "expansion_count": 1,
            "enemy_visible_units": 0, "enemy_visible_structures": 0,
            "enemy_army_analysis": {},
        }
        our_comp = {}
        structures = {"NEXUS": 1, "ASSIMILATOR": 2, "GATEWAY": 2, "CYBERNETICSCORE": 1}

        calc.update(features)
        action = engine.evaluate(
            calc.bias_vector, features,
            own_composition=our_comp,
            structures=structures,
        )

        assert action.type != ActionType.NOOP
        assert action.score > 0
        assert action.target != ""

    def test_engine_action_uses_biases(self):
        profile = StrategyLoader(_DATA_DIR).get_default("protoss")

        features = {
            "minerals": 500, "vespene": 300,
            "supply_left": 5, "supply_used": 25, "supply_cap": 30,
            "worker_count": 20, "army_count": 0,
            "game_time_seconds": 120, "expansion_count": 1,
            "enemy_visible_units": 0, "enemy_visible_structures": 0,
            "enemy_army_analysis": {},
        }
        structures = {"NEXUS": 1, "GATEWAY": 2, "CYBERNETICSCORE": 1}

        gateway_bias = dict(profile.initial_biases)
        gateway_bias["gateway_units"] = 0.9
        gateway_bias["stargate_units"] = 0.1
        gateway_bias["robo_units"] = 0.1
        engine = PriorityEngine(profile)
        action = engine.evaluate(gateway_bias, features, structures=structures)
        assert action.type in (ActionType.BUILD_UNIT, ActionType.RESEARCH_UPGRADE, ActionType.BUILD_STRUCTURE)
        assert action.target in ("STALKER", "ZEALOT", "SENTRY", "WARPGATERESEARCH", "GATEWAY")

        air_bias = dict(profile.initial_biases)
        air_bias["gateway_units"] = 0.1
        air_bias["stargate_units"] = 0.9
        air_bias["robo_units"] = 0.1
        engine2 = PriorityEngine(profile)
        action2 = engine2.evaluate(air_bias, features, structures=structures)
        assert action2.type in (ActionType.BUILD_UNIT, ActionType.BUILD_STRUCTURE, ActionType.RESEARCH_UPGRADE)
        assert action2.target in ("VOIDRAY", "PHOENIX", "STARGATE")

    def test_engine_supply_blocked_returns_eco_or_noop(self):
        profile = StrategyLoader(_DATA_DIR).get_default("protoss")
        calc = BiasCalculator(profile)
        engine = PriorityEngine(profile)

        features = {
            "minerals": 500, "vespene": 300,
            "supply_left": 0, "supply_used": 30, "supply_cap": 30,
            "worker_count": 30, "army_count": 0,
            "game_time_seconds": 120, "expansion_count": 1,
            "enemy_visible_units": 0, "enemy_visible_structures": 0,
            "enemy_army_analysis": {},
        }
        structures = {"NEXUS": 1, "PYLON": 1, "GATEWAY": 2}

        calc.update(features)
        action = engine.evaluate(
            calc.bias_vector, features, structures=structures,
        )
        assert action.type in (ActionType.BUILD_STRUCTURE, ActionType.ECO_ACTION, ActionType.NOOP)

    def test_engine_bias_updates_from_scouting(self):
        profile = _make_scouting_profile()
        calc = BiasCalculator(profile)

        features = {
            "game_time_seconds": 120, "supply_used": 30,
            "enemy_army_analysis": {"air_count": 8},
        }

        initial = calc.update({"game_time_seconds": 0})
        assert initial["stargate_units"] == 0.2

        updated = calc.update(features)
        assert updated["stargate_units"] > 0.2

    def test_fsm_surrender_blocks_engine(self):
        profile = StrategyLoader(_DATA_DIR).get_default("protoss")
        calc = BiasCalculator(profile)
        engine = PriorityEngine(profile)
        features = {
            "minerals": 0, "vespene": 0,
            "supply_left": 0, "supply_used": 15, "supply_cap": 15,
            "worker_count": 0, "army_count": 0,
            "game_time_seconds": 600, "expansion_count": 0,
            "enemy_visible_units": 0, "enemy_visible_structures": 0,
            "enemy_army_analysis": {},
        }
        calc.update(features)
        action = engine.evaluate(calc.bias_vector, features)
        assert action.type == ActionType.NOOP


def _make_scouting_profile() -> StrategyProfile:
    return StrategyProfile(
        name="test_scout",
        race="Protoss",
        initial_biases={"stargate_units": 0.2, "gateway_units": 0.5},
        scouting_adjustments=[
            ScoutingAdjustment(
                condition="enemy_army_analysis.air_count > 5",
                biases={"stargate_units": 0.3},
            ),
        ],
        priority_formulas={"STALKER": FormulaEntry(formula="0.5")},
        meta=MetaParams(bias_speed=1.0),
    )
