"""Formula evaluator — DSL for priority formulas and scouting conditions."""

import logging
import math
import re

logger = logging.getLogger(__name__)


def evaluate_condition(condition: str, features: dict) -> bool:
    if not condition or not isinstance(condition, str):
        return False

    resolved = _resolve_dots(condition, features)
    try:
        return bool(eval(resolved, {"__builtins__": {}}, features))
    except Exception:
        return False



def evaluate_formula(
    formula: str,
    bias_vector: dict[str, float],
    builtins: dict,
    extras: dict | None = None,
) -> float:
    if not formula or not isinstance(formula, str):
        return 0.0

    variables = dict(bias_vector)
    for k, v in builtins.items():
        variables[k] = v
    if extras:
        variables.update(extras)

    safe_builtins = {
        "abs": abs,
        "max": max,
        "min": min,
        "round": round,
        "True": True,
        "False": False,
    }

    converted = _convert_ternary(formula)

    try:
        result = eval(converted, {"__builtins__": safe_builtins}, variables)
        return max(0.0, float(result))
    except Exception as e:
        logger.warning("Formula eval failed [%s]: %s", formula, e)
        return 0.0


def _convert_ternary(formula: str) -> str:
    while "?" in formula:
        formula = _convert_one_ternary(formula)
    return formula


def _convert_one_ternary(formula: str) -> str:
    qpos = formula.find("?")
    if qpos == -1:
        return formula

    colon = _find_matching_colon(formula, qpos)
    if colon == -1:
        return formula

    cond_start, cond_text = _find_condition(formula, qpos)
    true_expr = formula[qpos + 1:colon].strip()

    if cond_start > 0:
        end = _find_outermost_close(formula)
        false_expr = formula[colon + 1:end].strip()
        before = formula[:cond_start]
        after = formula[end + 1:]
    else:
        raw_false = formula[colon + 1:]
        if formula.startswith("(") and raw_false.rstrip().endswith(")"):
            raw_false = raw_false.rstrip()[:-1]
        false_expr = raw_false.strip()
        before = ""
        after = ""

    replacement = f"({true_expr} if {cond_text} else {false_expr})"
    return before + replacement + after


def _find_matching_colon(formula: str, qpos: int) -> int:
    depth = 0
    for i in range(qpos + 1, len(formula)):
        if formula[i] == '(':
            depth += 1
        elif formula[i] == ')':
            depth -= 1
        elif formula[i] == ':' and depth == 0:
            return i
    return -1


def _find_condition(formula: str, qpos: int) -> tuple[int, str]:
    depth = 0
    for i in range(qpos - 1, -1, -1):
        c = formula[i]
        if c == ')':
            depth += 1
        elif c == '(':
            if depth == 0:
                cond_start = i
                cond_text = formula[cond_start:qpos]
                if cond_text.startswith('('):
                    cond_text = cond_text[1:].strip()
                return cond_start, cond_text.strip()
            depth -= 1
    return 0, formula[:qpos].strip()


def _find_outermost_close(formula: str) -> int:
    depth = 0
    for i in range(len(formula) - 1, -1, -1):
        if formula[i] == ')':
            if depth == 0:
                return i
            depth += 1
        elif formula[i] == '(':
            depth -= 1
    return len(formula) - 1


def prepare_builtins(
    features: dict,
    bot=None,
    *,
    own_composition: dict[str, int] | None = None,
    structures: dict[str, int] | None = None,
    completed_upgrades: set[str] | None = None,
) -> dict:
    def own_ratio(unit_name: str, category: str = "army") -> float:
        if not own_composition:
            return 0.0
        total = sum(own_composition.values())
        if total == 0:
            return 0.0
        count = own_composition.get(unit_name, 0)
        return count / total

    def has_structure(name: str) -> float:
        if not structures:
            return 0.0
        return float(structures.get(name, 0))

    def has_upgrade(name: str) -> float:
        if not completed_upgrades:
            return 0.0
        return 1.0 if name in completed_upgrades else 0.0

    def has_enemy() -> float:
        return 1.0 if features.get("enemy_visible_units", 0) > 0 else 0.0

    analysis = features.get("enemy_army_analysis", {}) or {}

    return {
        "own_ratio": own_ratio,
        "has_structure": has_structure,
        "has_upgrade": has_upgrade,
        "minerals": float(features.get("minerals", 0)),
        "vespene": float(features.get("vespene", 0)),
        "supply_left": float(features.get("supply_left", 0)),
        "supply_used": float(features.get("supply_used", 0)),
        "workers": float(features.get("worker_count", 0)),
        "game_time": float(features.get("game_time_seconds", 0)),
        "bases": float(features.get("expansion_count", 0)),
        "enemy_air": float(analysis.get("air_count", 0)),
        "enemy_ground_dps": float(analysis.get("ground_dps", 0)),
        "enemy_air_dps": float(analysis.get("air_dps", 0)),
        "enemy_mechanical": float(analysis.get("mechanical_count", 0)),
        "enemy_biological": float(analysis.get("biological_count", 0)),
        "enemy_armored": float(analysis.get("armored_count", 0)),
        "enemy_light": float(analysis.get("light_count", 0)),
        "enemy_massive": float(analysis.get("massive_count", 0)),
        "has_enemy": has_enemy(),
        "pi": math.pi,
        "e": math.e,
    }


_DOT_RE = re.compile(r'\b([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)+)\b')


def _resolve_dots(expr: str, features: dict) -> str:
    def _replacer(match):
        path = match.group(1)
        value = _dot_get(features, path)
        if isinstance(value, str):
            return repr(value)
        return str(value)
    return _DOT_RE.sub(_replacer, expr)


def _dot_get(d: dict, path: str):
    parts = path.split(".")
    current = d
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return 0
    return current
