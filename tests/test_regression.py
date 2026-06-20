"""Regression test: compare engine decisions against historical game snapshots."""

import json
from pathlib import Path

import pytest
from src.strategies.types import ActionType
from src.strategies.bias_calculator import BiasCalculator
from src.strategies.priority_engine import PriorityEngine
from src.strategies.loader import StrategyLoader

_DATA_DIR = Path(__file__).parent.parent / "src" / "data" / "strategies"
_REPORTS_DIR = Path(__file__).parent.parent / "reports"


def _load_latest_features() -> list[dict]:
    match_dirs = sorted(
        [d for d in _REPORTS_DIR.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    for md in match_dirs:
        fpath = md / "features.jsonl"
        if fpath.exists():
            features = []
            with open(fpath) as f:
                for line in f:
                    features.append(json.loads(line))
            if len(features) > 100:
                return features
    return []


class TestRegressionEngine:
    @pytest.mark.slow
    def test_engine_does_not_return_noop_in_normal_game(self):
        features_list = _load_latest_features()
        if not features_list:
            pytest.skip("No historical game data available")

        profile = StrategyLoader(_DATA_DIR).get_default("protoss")
        calc = BiasCalculator(profile)
        engine = PriorityEngine(profile)

        noop_count = 0
        total = 0

        for f in features_list[::10]:
            gt = f.get("game_time_seconds", 0)
            if gt < 30:
                continue

            calc.update(f)
            action = engine.evaluate(
                calc.bias_vector,
                f,
                own_composition=f.get("our_army_composition", {}),
                structures=f.get("our_structures", {}),
            )

            total += 1
            if action.type == ActionType.NOOP:
                noop_count += 1

        noop_rate = noop_count / total if total else 0
        assert noop_rate < 0.5, f"Engine returned NOOP {noop_rate:.0%} of the time"

    @pytest.mark.slow
    def test_engine_produces_build_actions(self):
        features_list = _load_latest_features()
        if not features_list:
            pytest.skip("No historical game data available")

        profile = StrategyLoader(_DATA_DIR).get_default("protoss")
        calc = BiasCalculator(profile)
        engine = PriorityEngine(profile)

        actions_seen = set()

        for f in features_list[::20]:
            gt = f.get("game_time_seconds", 0)
            if gt < 60:
                continue

            calc.update(f)
            action = engine.evaluate(
                calc.bias_vector,
                f,
                own_composition=f.get("our_army_composition", {}),
                structures=f.get("our_structures", {}),
            )

            if action.target:
                actions_seen.add((action.type.name, action.target))

        assert len(actions_seen) >= 2, f"Only {len(actions_seen)} unique actions produced"
        all_targets = {a[1] for a in actions_seen}
        assert len(all_targets) >= 2, f"Engine only produced one action type: {all_targets}"

    @pytest.mark.slow
    def test_biases_converge_to_nonzero_values(self):
        features_list = _load_latest_features()
        if not features_list:
            pytest.skip("No historical game data available")

        profile = StrategyLoader(_DATA_DIR).get_default("protoss")
        calc = BiasCalculator(profile)

        mid_game = [f for f in features_list if 240 < f.get("game_time_seconds", 0) < 360]
        if not mid_game:
            pytest.skip("No mid-game data")

        for f in mid_game[-5:]:
            calc.update(f)

        final = calc.bias_vector
        assert final["gateway_units"] > 0, "gateway_units bias is zero"
        assert all(0 <= v <= 1 for v in final.values()), "Biases outside [0,1]"

    @pytest.mark.slow
    def test_standard_macro_profile_loads_and_evaluates(self):
        profile = StrategyLoader(_DATA_DIR).get_default("protoss")
        assert profile.name == "standard_macro"
        assert len(profile.priority_formulas) >= 10

        engine = PriorityEngine(profile)
        bias = dict(profile.initial_biases)
        features = {
            "minerals": 500, "vespene": 300,
            "supply_left": 5, "supply_used": 25, "supply_cap": 30,
            "worker_count": 20, "army_count": 0,
            "game_time_seconds": 200, "expansion_count": 1,
            "enemy_visible_units": 0, "enemy_visible_structures": 0,
            "enemy_army_analysis": {},
        }
        structures = {"NEXUS": 1, "GATEWAY": 2, "CYBERNETICSCORE": 1}
        action = engine.evaluate(bias, features, structures=structures)
        assert action.type != ActionType.NOOP
