import pytest
from src.strategies.types import StrategyProfile, Action, ActionType, MetaParams, FormulaEntry
from src.strategies.priority_engine import PriorityEngine


def _make_profile(**overrides) -> StrategyProfile:
    defaults = {
        "name": "test",
        "race": "Protoss",
        "initial_biases": {"gateway_units": 0.6, "stargate_units": 0.4},
        "priority_formulas": {},
        "meta": MetaParams(),
    }
    defaults.update(overrides)
    formulas = defaults["priority_formulas"]
    if formulas and isinstance(next(iter(formulas.values()), None), str):
        defaults["priority_formulas"] = {
            k: FormulaEntry(formula=v) for k, v in formulas.items()
        }
    return StrategyProfile(**defaults)


class TestPriorityEngine:
    def test_selects_highest_scoring_action(self):
        profile = _make_profile(priority_formulas={
            "STALKER": "0.8",
            "ZEALOT": "0.3",
            "VOIDRAY": "0.5",
        })
        engine = PriorityEngine(profile)
        bias = {"gateway_units": 0.6, "stargate_units": 0.4}
        features = {
            "minerals": 500, "vespene": 300,
            "supply_left": 5, "supply_used": 25, "worker_count": 20,
            "game_time_seconds": 200, "expansion_count": 2,
            "enemy_visible_units": 0, "enemy_army_analysis": {},
        }
        action = engine.evaluate(bias, features)
        assert action.type == ActionType.BUILD_UNIT
        assert action.target == "STALKER"
        assert action.score == 0.8

    def test_ignores_formula_not_in_categories(self):
        profile = _make_profile(priority_formulas={"UNKNOWN_UNIT": "0.9"})
        engine = PriorityEngine(profile)
        bias = {}
        features = {"minerals": 500, "supply_left": 5, "game_time_seconds": 200}
        action = engine.evaluate(bias, features)
        assert action.type == ActionType.NOOP

    def test_filter_blocked_actions_no_supply(self):
        profile = _make_profile(priority_formulas={"STALKER": "0.9", "ZEALOT": "0.8"})
        engine = PriorityEngine(profile)
        bias = {}
        features = {
            "minerals": 500, "vespene": 300,
            "supply_left": 0, "supply_used": 200, "worker_count": 20,
            "game_time_seconds": 300, "expansion_count": 3,
            "enemy_visible_units": 0, "enemy_army_analysis": {},
        }
        action = engine.evaluate(bias, features)
        assert action.type == ActionType.NOOP

    def test_tie_broken_deterministically(self):
        profile = _make_profile(priority_formulas={
            "ZEALOT": "0.7",
            "STALKER": "0.7",
        })
        engine = PriorityEngine(profile)
        bias = {}
        features = {
            "minerals": 500, "vespene": 300,
            "supply_left": 5, "supply_used": 30, "worker_count": 20,
            "game_time_seconds": 200, "expansion_count": 2,
            "enemy_visible_units": 0, "enemy_army_analysis": {},
        }
        action = engine.evaluate(bias, features)
        assert action.type == ActionType.BUILD_UNIT
        assert action.target == "STALKER"

    def test_no_actions_returns_noop(self):
        profile = _make_profile(priority_formulas={})
        engine = PriorityEngine(profile)
        action = engine.evaluate({}, {"minerals": 0, "supply_left": 0, "game_time_seconds": 0})
        assert action.type == ActionType.NOOP
        assert action.score == 0.0

    def test_bias_affects_score(self):
        profile = _make_profile(priority_formulas={
            "STALKER": "gateway_units * 0.8",
            "VOIDRAY": "stargate_units * 0.9",
        })
        engine = PriorityEngine(profile)
        features = {
            "minerals": 500, "vespene": 300,
            "supply_left": 10, "supply_used": 30, "worker_count": 20,
            "game_time_seconds": 200, "expansion_count": 2,
            "enemy_visible_units": 0, "enemy_army_analysis": {},
        }

        gateway_bias = {"gateway_units": 0.9, "stargate_units": 0.1}
        action_gw = engine.evaluate(gateway_bias, features)
        assert action_gw.target == "STALKER"

        stargate_bias = {"gateway_units": 0.1, "stargate_units": 0.9}
        action_sg = PriorityEngine(profile).evaluate(stargate_bias, features)
        assert action_sg.target == "VOIDRAY"

    def test_structure_action_classified(self):
        profile = _make_profile(priority_formulas={
            "GATEWAY": "0.5",
            "CYBERNETICSCORE": "0.7",
        })
        engine = PriorityEngine(profile)
        bias = {}
        features = {
            "minerals": 500, "vespene": 300,
            "supply_left": 5, "supply_used": 25, "worker_count": 20,
            "game_time_seconds": 60, "expansion_count": 1,
            "enemy_visible_units": 0, "enemy_army_analysis": {},
        }
        action = engine.evaluate(bias, features)
        assert action.type == ActionType.BUILD_STRUCTURE
        assert action.target == "CYBERNETICSCORE"

    def test_upgrade_action_classified(self):
        profile = _make_profile(priority_formulas={
            "WARPGATERESEARCH": "0.9",
        })
        engine = PriorityEngine(profile)
        bias = {}
        features = {
            "minerals": 200, "vespene": 100,
            "supply_left": 5, "supply_used": 30, "worker_count": 20,
            "game_time_seconds": 200, "expansion_count": 2,
            "enemy_visible_units": 0, "enemy_army_analysis": {},
        }
        action = engine.evaluate(bias, features)
        assert action.type == ActionType.RESEARCH_UPGRADE
        assert action.target == "WARPGATERESEARCH"

    def test_eco_action_classified(self):
        profile = _make_profile(priority_formulas={"PROBE": "0.9"})
        engine = PriorityEngine(profile)
        bias = {}
        features = {
            "minerals": 100, "vespene": 0,
            "supply_left": 5, "supply_used": 12, "worker_count": 12,
            "game_time_seconds": 20, "expansion_count": 1,
            "enemy_visible_units": 0, "enemy_army_analysis": {},
        }
        action = engine.evaluate(bias, features)
        assert action.type == ActionType.ECO_ACTION

    def test_formula_with_own_ratio(self):
        profile = _make_profile(priority_formulas={
            "STALKER": "gateway_units * 0.6 * (1 - own_ratio('STALKER'))",
        })
        engine = PriorityEngine(profile)
        bias = {"gateway_units": 0.8}
        features = {
            "minerals": 500, "vespene": 300,
            "supply_left": 5, "supply_used": 30, "worker_count": 20,
            "game_time_seconds": 200, "expansion_count": 2,
            "enemy_visible_units": 0, "enemy_army_analysis": {},
        }
        own_comp = {"STALKER": 10, "ZEALOT": 10}
        action = engine.evaluate(bias, features, own_composition=own_comp)
        assert action.target == "STALKER"
        assert action.score == pytest.approx(0.8 * 0.6 * 0.5)


class TestTechTreeFiltering:
    def test_action_with_satisfied_requires_is_evaluated(self):
        profile = _make_profile(priority_formulas={
            "COLOSSUS": FormulaEntry(formula="0.9", requires=["ROBOTICSBAY"]),
        })
        engine = PriorityEngine(profile)
        features = {
            "minerals": 500, "vespene": 300,
            "supply_left": 5, "supply_used": 30, "worker_count": 20,
            "game_time_seconds": 200, "expansion_count": 2,
            "enemy_visible_units": 0, "enemy_army_analysis": {},
        }
        structures = {"ROBOTICSBAY": 1}
        action = engine.evaluate({"robo_units": 0.8}, features, structures=structures)
        assert action.target == "COLOSSUS"
        assert action.score > 0

    def test_action_with_missing_requires_is_filtered(self):
        profile = _make_profile(priority_formulas={
            "COLOSSUS": FormulaEntry(formula="0.9", requires=["ROBOTICSBAY"]),
            "STALKER": FormulaEntry(formula="0.5"),
        })
        engine = PriorityEngine(profile)
        features = {
            "minerals": 500, "vespene": 300,
            "supply_left": 5, "supply_used": 30, "worker_count": 20,
            "game_time_seconds": 200, "expansion_count": 2,
            "enemy_visible_units": 0, "enemy_army_analysis": {},
        }
        action = engine.evaluate({"robo_units": 0.8}, features, structures={})
        assert action.target == "STALKER"

    def test_backward_compatible_string_formula_no_requires(self):
        profile = _make_profile(priority_formulas={"STALKER": "0.9"})
        engine = PriorityEngine(profile)
        features = {
            "minerals": 500, "vespene": 300,
            "supply_left": 5, "supply_used": 30, "worker_count": 20,
            "game_time_seconds": 200, "expansion_count": 2,
            "enemy_visible_units": 0, "enemy_army_analysis": {},
        }
        action = engine.evaluate({}, features)
        assert action.target == "STALKER"


class TestMomentum:
    def test_momentum_boosts_same_action(self):
        profile = _make_profile(priority_formulas={
            "STALKER": FormulaEntry(formula="0.5"),
            "ZEALOT": FormulaEntry(formula="0.48"),
        })
        engine = PriorityEngine(profile)
        features = {
            "minerals": 500, "vespene": 300,
            "supply_left": 5, "supply_used": 30, "worker_count": 20,
            "game_time_seconds": 200, "expansion_count": 2,
            "enemy_visible_units": 0, "enemy_army_analysis": {},
        }
        prev = Action(type=ActionType.BUILD_UNIT, target="STALKER", score=0.5)
        action = engine.evaluate({}, features, prev_action=prev)
        assert action.target == "STALKER"
        assert action.score == pytest.approx(0.5 * 1.15)

    def test_momentum_ignored_when_prev_is_none(self):
        profile = _make_profile(priority_formulas={
            "STALKER": FormulaEntry(formula="0.5"),
            "ZEALOT": FormulaEntry(formula="0.48"),
        })
        engine = PriorityEngine(profile)
        features = {
            "minerals": 500, "vespene": 300,
            "supply_left": 5, "supply_used": 30, "worker_count": 20,
            "game_time_seconds": 200, "expansion_count": 2,
            "enemy_visible_units": 0, "enemy_army_analysis": {},
        }
        action = engine.evaluate({}, features, prev_action=None)
        assert action.target == "STALKER"
        assert action.score == 0.5

    def test_momentum_ignored_when_prev_is_noop(self):
        profile = _make_profile(priority_formulas={
            "STALKER": FormulaEntry(formula="0.5"),
            "ZEALOT": FormulaEntry(formula="0.48"),
        })
        engine = PriorityEngine(profile)
        features = {
            "minerals": 500, "vespene": 300,
            "supply_left": 5, "supply_used": 30, "worker_count": 20,
            "game_time_seconds": 200, "expansion_count": 2,
            "enemy_visible_units": 0, "enemy_army_analysis": {},
        }
        prev = Action(type=ActionType.NOOP, target="", score=0.0)
        action = engine.evaluate({}, features, prev_action=prev)
        assert action.target == "STALKER"
        assert action.score == 0.5

    def test_momentum_applied_to_correct_engine_only(self):
        profile = _make_profile(priority_formulas={
            "STALKER": FormulaEntry(formula="0.5"),
            "VOIDRAY": FormulaEntry(formula="0.49"),
        })
        engine = PriorityEngine(profile)
        features = {
            "minerals": 500, "vespene": 300,
            "supply_left": 5, "supply_used": 30, "worker_count": 20,
            "game_time_seconds": 200, "expansion_count": 2,
            "enemy_visible_units": 0, "enemy_army_analysis": {},
        }
        prev = Action(type=ActionType.BUILD_UNIT, target="VOIDRAY", score=0.49)
        action = engine.evaluate({}, features, prev_action=prev)
        assert action.target == "VOIDRAY"
        assert action.score == pytest.approx(0.49 * 1.15)
