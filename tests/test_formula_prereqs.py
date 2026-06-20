from src.strategies.formula import evaluate_formula, prepare_builtins


def test_forge_formula_zero_without_gateway():
    formula = "ground_upgrades * has_structure('GATEWAY') * (1 - has_structure('FORGE')) * 0.5"
    features = {
        "minerals": 400, "vespene": 200, "supply_left": 5, "supply_used": 20,
        "worker_count": 16, "game_time_seconds": 120, "expansion_count": 1,
        "enemy_visible_units": 5, "enemy_army_analysis": {},
    }
    structures = {}
    builtins = prepare_builtins(features, structures=structures)
    bias = {"ground_upgrades": 0.8}
    score = evaluate_formula(formula, bias, builtins)
    assert score == 0.0


def test_forge_formula_positive_with_gateway():
    formula = "ground_upgrades * has_structure('GATEWAY') * (1 - has_structure('FORGE')) * 0.5"
    features = {
        "minerals": 400, "vespene": 200, "supply_left": 5, "supply_used": 20,
        "worker_count": 16, "game_time_seconds": 120, "expansion_count": 1,
        "enemy_visible_units": 5, "enemy_army_analysis": {},
    }
    structures = {"GATEWAY": 1}
    builtins = prepare_builtins(features, structures=structures)
    bias = {"ground_upgrades": 0.8}
    score = evaluate_formula(formula, bias, builtins)
    assert score == 0.4


def test_robo_formula_without_core_returns_zero_spite_having_prerequisite():
    formula = "robo_units * (has_structure('CYBERNETICSCORE') * (1 - max(0, 0 - 1) / (1 + 1)))"
    features = {
        "minerals": 400, "vespene": 300, "supply_left": 5, "supply_used": 20,
        "worker_count": 16, "game_time_seconds": 120, "expansion_count": 1,
        "enemy_visible_units": 5, "enemy_army_analysis": {},
    }
    structures = {"GATEWAY": 1}
    builtins = prepare_builtins(features, structures=structures)
    bias = {"robo_units": 0.8}
    score = evaluate_formula(formula, bias, builtins)
    assert score == 0.0


def test_robo_formula_positive_with_core():
    formula = "robo_units * (has_structure('CYBERNETICSCORE') * (1 - max(0, 0 - 1) / (1 + 1)))"
    features = {
        "minerals": 400, "vespene": 300, "supply_left": 5, "supply_used": 20,
        "worker_count": 16, "game_time_seconds": 120, "expansion_count": 1,
        "enemy_visible_units": 5, "enemy_army_analysis": {},
    }
    structures = {"GATEWAY": 1, "CYBERNETICSCORE": 1}
    builtins = prepare_builtins(features, structures=structures)
    bias = {"robo_units": 0.8}
    score = evaluate_formula(formula, bias, builtins)
    assert score > 0.0


def test_twilight_formula_zero_without_core():
    formula = "gateway_units * has_structure('CYBERNETICSCORE') * 0.3 * (1 - has_structure('TWILIGHTCOUNCIL')) * 0.8"
    features = {
        "minerals": 400, "vespene": 300, "supply_left": 5, "supply_used": 20,
        "worker_count": 16, "game_time_seconds": 120, "expansion_count": 1,
        "enemy_visible_units": 5, "enemy_army_analysis": {},
    }
    structures = {"GATEWAY": 1}
    builtins = prepare_builtins(features, structures=structures)
    bias = {"gateway_units": 0.8}
    score = evaluate_formula(formula, bias, builtins)
    assert score == 0.0


def test_stargate_formula_zero_without_core():
    formula = "stargate_units * (has_structure('CYBERNETICSCORE') * (1 - max(0, 0 - 1) / (1 + 1)))"
    features = {
        "minerals": 400, "vespene": 300, "supply_left": 5, "supply_used": 20,
        "worker_count": 16, "game_time_seconds": 120, "expansion_count": 1,
        "enemy_visible_units": 5, "enemy_army_analysis": {},
    }
    structures = {"GATEWAY": 1}
    builtins = prepare_builtins(features, structures=structures)
    bias = {"stargate_units": 0.6}
    score = evaluate_formula(formula, bias, builtins)
    assert score == 0.0
