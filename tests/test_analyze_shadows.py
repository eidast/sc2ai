import json
import pytest
from scripts.analyze_shadows import (
    _load_jsonl,
    _compute_overview,
    _compute_agreement,
    _compute_action_distribution,
    _compute_bias_evolution,
    _compute_timeline,
    _format_text,
)


def _write_jsonl(tmp_path, filename, records):
    p = tmp_path / filename
    with open(p, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return str(p)


class TestLoadJsonl:
    def test_loads_valid_file(self, tmp_path):
        records = [{"a": 1}, {"a": 2}]
        path = _write_jsonl(tmp_path, "test.jsonl", records)
        result = _load_jsonl(path)
        assert len(result) == 2

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            _load_jsonl("/nonexistent/path.jsonl")


class TestOverview:
    def test_basic_overview(self):
        decisions = [
            {"time": 10, "step": 0, "strategic_state": "DEFEND", "override_source": "none"},
            {"time": 20, "step": 1, "strategic_state": "ATTACK", "override_source": "early_game_build_order"},
        ]
        result = _compute_overview(decisions, 2)
        assert result["total_steps"] == 2
        assert result["game_time"] == 20
        assert result["override_rate"] == 50
        assert result["strategic_states"]["DEFEND"] == 50

    def test_empty_decisions(self):
        result = _compute_overview([], 0)
        assert result["total_steps"] == 0


class TestAgreement:
    def test_agreement_matrix(self):
        decisions = [
            {
                "time": 10, "step": 0,
                "heuristic_profile": "standard_macro",
                "utility": {"recommended_action": {"type": "BUILD_UNIT", "target": "STALKER", "score": 0.8}},
                "shadow_predictions": [
                    {"profile": "stargate_open", "recommended_action": {"type": "BUILD_UNIT", "target": "VOIDRAY", "score": 0.9}},
                ],
            },
            {
                "time": 20, "step": 1,
                "heuristic_profile": "standard_macro",
                "utility": {"recommended_action": {"type": "BUILD_UNIT", "target": "STALKER", "score": 0.8}},
                "shadow_predictions": [
                    {"profile": "stargate_open", "recommended_action": {"type": "BUILD_UNIT", "target": "STALKER", "score": 0.7}},
                ],
            },
        ]
        result = _compute_agreement(decisions)
        profiles = result["profiles"]
        assert "standard_macro" in profiles
        assert "stargate_open" in profiles
        assert result["matrix"]["standard_macro"]["stargate_open"] == 50.0

    def test_no_shadow_predictions(self):
        decisions = [
            {
                "time": 10, "step": 0,
                "heuristic_profile": "standard_macro",
                "utility": {"recommended_action": {"type": "BUILD_UNIT", "target": "STALKER", "score": 0.8}},
                "shadow_predictions": [],
            },
        ]
        result = _compute_agreement(decisions)
        assert len(result["profiles"]) <= 1


class TestActionDistribution:
    def test_top_actions(self):
        decisions = [
            {
                "time": 10, "step": 0,
                "heuristic_profile": "standard_macro",
                "utility": {"recommended_action": {"type": "BUILD_UNIT", "target": "STALKER", "score": 0.8}},
                "shadow_predictions": [],
            },
            {
                "time": 20, "step": 1,
                "heuristic_profile": "standard_macro",
                "utility": {"recommended_action": {"type": "BUILD_UNIT", "target": "STALKER", "score": 0.9}},
                "shadow_predictions": [],
            },
        ]
        result = _compute_action_distribution(decisions)
        assert "standard_macro" in result
        assert result["standard_macro"][0]["target"] == "STALKER"
        assert result["standard_macro"][0]["pct"] == 100.0


class TestBiasEvolution:
    def test_bias_delta(self):
        decisions = [
            {"utility": {"bias_vector": {"gateway_units": 0.8, "stargate_units": 0.2}}},
            {"utility": {"bias_vector": {"gateway_units": 0.6, "stargate_units": 0.4}}},
        ]
        result = _compute_bias_evolution(decisions)
        assert result["gateway_units"]["initial"] == 0.8
        assert result["gateway_units"]["final"] == 0.6
        assert result["gateway_units"]["delta"] == -0.2

    def test_no_bias_returns_empty(self):
        decisions = [{"utility": {}}]
        result = _compute_bias_evolution(decisions)
        assert result == {}


class TestTimeline:
    def test_state_transitions(self):
        decisions = [
            {"time": 10, "step": 0, "strategic_state": "DEFEND", "override_source": "none", "shadow_predictions": []},
            {"time": 20, "step": 1, "strategic_state": "ATTACK", "override_source": "none", "shadow_predictions": []},
        ]
        result = _compute_timeline(decisions)
        assert any("DEFEND → ATTACK" in e["event"] for e in result)

    def test_first_divergence(self):
        decisions = [
            {
                "time": 10, "step": 0,
                "heuristic_profile": "standard_macro",
                "utility": {"recommended_action": {"type": "BUILD_UNIT", "target": "STALKER", "score": 0.8}},
                "shadow_predictions": [
                    {"profile": "stargate_open", "recommended_action": {"type": "BUILD_UNIT", "target": "VOIDRAY", "score": 0.9}},
                ],
                "override_source": "none",
                "strategic_state": "DEFEND",
            },
        ]
        result = _compute_timeline(decisions)
        assert any("First divergence" in e["event"] for e in result)


class TestFormatText:
    def test_format_produces_output(self):
        results = {
            "overview": {"total_steps": 10, "game_time": 100, "strategic_states": {"DEFEND": 100.0}, "override_rate": 10.0},
            "agreement": {"profiles": [], "matrix": {}},
            "action_distribution": {},
            "bias_evolution": {},
            "timeline": [],
        }
        output = _format_text(results)
        assert "SHADOW ANALYSIS" in output
        assert "10" in output
