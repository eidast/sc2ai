import pytest
from src.strategies.formula import evaluate_formula, evaluate_condition, prepare_builtins


class TestEvaluateFormula:
    def test_simple_addition(self):
        result = evaluate_formula("0.5 + 0.3", {"x": 0.5}, {})
        assert result == 0.8

    def test_multiplication(self):
        result = evaluate_formula("2.0 * 3.0", {}, {})
        assert result == 6.0

    def test_division(self):
        result = evaluate_formula("6.0 / 2.0", {}, {})
        assert result == 3.0

    def test_division_by_zero_returns_zero(self):
        result = evaluate_formula("6.0 / 0.0", {}, {})
        assert result == 0.0

    def test_subtraction(self):
        result = evaluate_formula("1.0 - 0.7", {}, {})
        assert result == pytest.approx(0.3)

    def test_parentheses(self):
        result = evaluate_formula("(0.5 + 0.3) * 2.0", {}, {})
        assert result == 1.6

    def test_uses_bias_variable(self):
        bias = {"gateway_units": 0.6}
        result = evaluate_formula("gateway_units * 0.5", bias, {})
        assert result == 0.3

    def test_uses_builtin_variable(self):
        builtins = {"minerals": 500.0}
        result = evaluate_formula("minerals > 300 ? 0.5 : 0.1", {}, builtins)
        assert result == 0.5

    def test_ternary_false_branch(self):
        builtins = {"minerals": 200.0}
        result = evaluate_formula("minerals > 300 ? 0.5 : 0.1", {}, builtins)
        assert result == 0.1

    def test_max_function(self):
        result = evaluate_formula("max(0.3, 0.8)", {}, {})
        assert result == 0.8

    def test_max_with_variables(self):
        bias = {"a": 0.2, "b": 0.9}
        result = evaluate_formula("max(a, b)", bias, {})
        assert result == 0.9

    def test_recursive_expression(self):
        bias = {"gw": 0.6, "robo": 0.4}
        result = evaluate_formula("gw * 0.5 + robo * 0.3", bias, {})
        assert result == pytest.approx(0.6 * 0.5 + 0.4 * 0.3)

    def test_callable_builtin(self):
        def fake_ratio(name):
            return 0.25 if name == "STALKER" else 0.0

        builtins = {"own_ratio": fake_ratio}
        result = evaluate_formula("(1 - own_ratio('STALKER')) * 0.6", {}, builtins)
        assert result == pytest.approx(0.45)

    def test_invalid_formula_returns_zero(self):
        result = evaluate_formula("this +++ is ~~~ broken", {}, {})
        assert result == 0.0

    def test_empty_formula_returns_zero(self):
        result = evaluate_formula("", {}, {})
        assert result == 0.0

    def test_none_formula_returns_zero(self):
        result = evaluate_formula(None, {}, {})
        assert result == 0.0

    def test_unknown_variable_returns_zero(self):
        result = evaluate_formula("unknown_var * 2.0", {}, {})
        assert result == 0.0

    def test_result_never_negative(self):
        result = evaluate_formula("-5.0", {}, {})
        assert result == 0.0

    def test_complex_formula_with_own_ratio(self):
        bias = {"gateway_units": 0.6, "robo_units": 0.3}
        builtins = {"own_ratio": lambda name: 0.2 if name == "STALKER" else 0.0, "minerals": 300}
        result = evaluate_formula(
            "(gateway_units * 0.6 + (1 - robo_units) * 0.3) * (1 - own_ratio('STALKER'))",
            bias,
            builtins,
        )
        expected = (0.6 * 0.6 + (1 - 0.3) * 0.3) * (1 - 0.2)
        assert result == pytest.approx(expected)

    def test_minerals_condition_with_builtins(self):
        features = {"minerals": 450}
        builtins = prepare_builtins(features)
        result = evaluate_formula("minerals > 300 ? 0.5 : 0.2", {}, builtins)
        assert result == 0.5


class TestEvaluateCondition:
    def test_simple_greater_than_true(self):
        features = {"enemy_army_analysis": {"air_count": 8}}
        result = evaluate_condition("enemy_army_analysis.air_count > 5", features)
        assert result is True

    def test_simple_greater_than_false(self):
        features = {"enemy_army_analysis": {"air_count": 3}}
        result = evaluate_condition("enemy_army_analysis.air_count > 5", features)
        assert result is False

    def test_equal_comparison(self):
        features = {"supply_used": 200}
        result = evaluate_condition("supply_used == 200", features)
        assert result is True

    def test_not_equal(self):
        features = {"supply_used": 150}
        result = evaluate_condition("supply_used != 200", features)
        assert result is True

    def test_nested_feature_access(self):
        features = {"enemy_army_analysis": {"mechanical_count": 5, "biological_count": 2}}
        result = evaluate_condition(
            "enemy_army_analysis.mechanical_count > enemy_army_analysis.biological_count",
            features,
        )
        assert result is True

    def test_unknown_field_returns_false(self):
        features = {"enemy_army_analysis": {"air_count": 5}}
        result = evaluate_condition("enemy_army_analysis.unknown_field > 3", features)
        assert result is False

    def test_empty_condition_returns_false(self):
        result = evaluate_condition("", {})
        assert result is False


class TestPrepareBuiltins:
    def test_basic_builtins_present(self):
        features = {
            "minerals": 400,
            "vespene": 200,
            "supply_left": 5,
            "supply_used": 30,
            "worker_count": 22,
            "game_time_seconds": 120.0,
            "expansion_count": 2,
            "enemy_visible_units": 3,
            "enemy_army_analysis": {"air_count": 4, "ground_dps": 50.0, "air_dps": 20.0},
        }
        b = prepare_builtins(features)
        assert b["minerals"] == 400.0
        assert b["vespene"] == 200.0
        assert b["supply_left"] == 5.0
        assert b["workers"] == 22.0
        assert b["game_time"] == 120.0
        assert b["bases"] == 2.0
        assert b["enemy_air"] == 4.0
        assert b["has_enemy"] == 1.0

    def test_callable_builtins(self):
        features = {"minerals": 100}
        own_comp = {"STALKER": 5, "ZEALOT": 5}
        structures = {"GATEWAY": 2}
        upgrades = {"WARPGATERESEARCH"}

        b = prepare_builtins(
            features,
            own_composition=own_comp,
            structures=structures,
            completed_upgrades=upgrades,
        )
        assert b["own_ratio"]("STALKER") == 0.5
        assert b["own_ratio"]("MISSING") == 0.0
        assert b["has_structure"]("GATEWAY") == 2.0
        assert b["has_structure"]("FORGE") == 0.0
        assert b["has_upgrade"]("WARPGATERESEARCH") == 1.0
        assert b["has_upgrade"]("BLINKTECH") == 0.0

    def test_no_enemy_returns_zero(self):
        features = {"enemy_visible_units": 0}
        b = prepare_builtins(features)
        assert b["has_enemy"] == 0.0

    def test_missing_analysis_defaults(self):
        features = {}
        b = prepare_builtins(features)
        assert b["enemy_air"] == 0.0
        assert b["enemy_ground_dps"] == 0.0


class TestYamlFormulaComplex:
    def test_probe_formula(self):
        bias = {}
        builtins = {"workers": 12.0}
        result = evaluate_formula("(workers < 70 ? (1 - workers / 70) : 0)", bias, builtins)
        assert result == pytest.approx(1 - 12/70)

    def test_probe_formula_at_max(self):
        bias = {}
        builtins = {"workers": 70.0}
        result = evaluate_formula("(workers < 70 ? (1 - workers / 70) : 0)", bias, builtins)
        assert result == 0.0

    def test_pylon_formula_blocked(self):
        bias = {}
        builtins = {"supply_left": 2.0}
        result = evaluate_formula("supply_left < 4 ? 2.0 : 0.1", bias, builtins)
        assert result == 2.0

    def test_pylon_formula_not_blocked(self):
        bias = {}
        builtins = {"supply_left": 5.0}
        result = evaluate_formula("supply_left < 4 ? 2.0 : 0.1", bias, builtins)
        assert result == 0.1

    def test_gateway_formula(self):
        bias = {"gateway_units": 0.6, "robo_units": 0.3}
        builtins = {"bases": 1.0, "has_structure": lambda name: 0.0}
        formula = "(gateway_units + (1 - robo_units) * 0.3) * (bases < 1 ? 1 : (bases * 3 - (has_structure('GATEWAY') * 2)) / (bases * 3 + 1))"
        result = evaluate_formula(formula, bias, builtins)
        assert result > 0.5

    def test_nexus_formula(self):
        bias = {"fast_expand": 0.6}
        builtins = {"minerals": 600.0}
        result = evaluate_formula("fast_expand * 0.6 + (minerals > 500 ? 0.4 : 0)", bias, builtins)
        assert result == pytest.approx(0.6 * 0.6 + 0.4)

    def test_forge_formula_poor(self):
        bias = {"ground_upgrades": 0.7}
        builtins = {"minerals": 200.0, "has_structure": lambda name: 0.0}
        result = evaluate_formula("ground_upgrades * (1 - has_structure('FORGE')) * (minerals > 300 ? 0.5 : 0.2)", bias, builtins)
        assert result == pytest.approx(0.7 * 1 * 0.2)

    def test_twilight_formula(self):
        bias = {"gateway_units": 0.6}
        builtins = {"minerals": 400.0, "vespene": 150.0, "has_structure": lambda name: 0.0}
        result = evaluate_formula("gateway_units * 0.3 * (1 - has_structure('TWILIGHTCOUNCIL')) * (minerals > 300 and vespene > 100 ? 0.8 : 0.1)", bias, builtins)
        assert result == pytest.approx(0.6 * 0.3 * 1 * 0.8)

    def test_assimilator_formula(self):
        bias = {"gas_heavy": 0.5}
        builtins = {"bases": 2.0, "has_structure": lambda name: 1.0}
        result = evaluate_formula("gas_heavy * (has_structure('ASSIMILATOR') < bases * 2 ? 1 : 0)", bias, builtins)
        assert result == 0.5  # 1 < 4 is True, so ternary returns 1

    def test_warpgate_formula(self):
        bias = {"gateway_units": 0.7}
        builtins = {"supply_used": 20.0, "has_structure": lambda name: 1.0, "has_upgrade": lambda name: 0.0}
        result = evaluate_formula("gateway_units * (1 - has_upgrade('WARPGATERESEARCH')) * has_structure('CYBERNETICSCORE')", bias, builtins)
        assert result == 0.7

    def test_stalker_formula(self):
        bias = {"gateway_units": 0.6, "robo_units": 0.3}
        builtins = {"own_ratio": lambda name: 0.2 if name == "STALKER" else 0.0}
        formula = "(gateway_units * 0.6 + (1 - robo_units) * 0.3) * (1 - own_ratio('STALKER'))"
        result = evaluate_formula(formula, bias, builtins)
        expected = (0.6 * 0.6 + (1 - 0.3) * 0.3) * (1 - 0.2)
        assert result == pytest.approx(expected)
