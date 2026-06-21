import pytest
from src.strategies.types import StrategyProfile, ScoutingAdjustment, MetaParams, FormulaEntry
from src.strategies.bias_calculator import BiasCalculator


def _make_profile(**overrides) -> StrategyProfile:
    defaults = {
        "name": "test",
        "race": "Protoss",
        "initial_biases": {"gateway_units": 0.5, "stargate_units": 0.3},
        "scouting_adjustments": [],
        "priority_formulas": {},
        "meta": MetaParams(bias_speed=0.3, scout_decay_rate=0.05),
    }
    defaults.update(overrides)
    formulas = defaults["priority_formulas"]
    if formulas and isinstance(next(iter(formulas.values()), None), str):
        defaults["priority_formulas"] = {
            k: FormulaEntry(formula=v) for k, v in formulas.items()
        }
    return StrategyProfile(**defaults)


class TestBiasCalculatorInit:
    def test_initializes_biases_from_profile(self):
        profile = _make_profile(initial_biases={"gateway_units": 0.6, "robo_units": 0.4})
        calc = BiasCalculator(profile)
        result = calc.update({})
        assert result["gateway_units"] == 0.6
        assert result["robo_units"] == 0.4

    def test_bias_vector_is_copy(self):
        calc = BiasCalculator(_make_profile())
        calc.update({})
        vec = calc.bias_vector
        vec["gateway_units"] = 0.9
        assert calc.bias_vector["gateway_units"] == 0.5


class TestBiasCalculatorAdjustments:
    def test_single_adjustment_applied(self):
        profile = _make_profile(
            initial_biases={"gateway_units": 0.5},
            scouting_adjustments=[
                ScoutingAdjustment(
                    condition="supply_used > 10",
                    biases={"gateway_units": 0.3},
                ),
            ],
        )
        calc = BiasCalculator(profile)
        features = {"supply_used": 15, "game_time_seconds": 120}
        result = calc.update(features)
        assert result["gateway_units"] > 0.5

    def test_adjustment_not_matching_condition(self):
        profile = _make_profile(
            initial_biases={"gateway_units": 0.5},
            scouting_adjustments=[
                ScoutingAdjustment(
                    condition="supply_used > 100",
                    biases={"gateway_units": 0.5},
                ),
            ],
        )
        calc = BiasCalculator(profile)
        features = {"supply_used": 15, "game_time_seconds": 120}
        result = calc.update(features)
        assert result["gateway_units"] == 0.5

    def test_multiple_adjustments_cumulative(self):
        profile = _make_profile(
            initial_biases={"gateway_units": 0.5, "stargate_units": 0.5},
            scouting_adjustments=[
                ScoutingAdjustment(condition="True", biases={"gateway_units": 0.2}),
                ScoutingAdjustment(condition="True", biases={"stargate_units": -0.2}),
            ],
        )
        calc = BiasCalculator(profile)
        features = {"game_time_seconds": 120}
        result = calc.update(features)
        assert result["gateway_units"] > 0.5
        assert result["stargate_units"] < 0.5

    def test_confidence_affects_adjustment(self):
        profile = _make_profile(
            initial_biases={"gateway_units": 0.5},
            scouting_adjustments=[
                ScoutingAdjustment(condition="True", biases={"gateway_units": 0.4}),
            ],
        )
        calc = BiasCalculator(profile)
        features = {"game_time_seconds": 120}

        high_conf = {"marine": {"last_seen": 120, "confidence": 1.0}}
        result_high = calc.update(features, scout_metadata=high_conf)
        assert result_high["gateway_units"] > 0.5

        calc2 = BiasCalculator(profile)
        low_conf = {"marine": {"last_seen": 120, "confidence": 0.1}}
        result_low = calc2.update(features, scout_metadata=low_conf)
        assert result_high["gateway_units"] > result_low["gateway_units"]


class TestBiasCalculatorClamping:
    def test_clamps_at_one(self):
        profile = _make_profile(
            initial_biases={"gateway_units": 0.95},
            scouting_adjustments=[
                ScoutingAdjustment(condition="True", biases={"gateway_units": 0.5}),
            ],
            meta=MetaParams(bias_speed=1.0),
        )
        calc = BiasCalculator(profile)
        result = calc.update({"game_time_seconds": 120})
        assert result["gateway_units"] <= 1.0
        assert result["gateway_units"] > 0.95

    def test_clamps_at_zero(self):
        profile = _make_profile(
            initial_biases={"gateway_units": 0.05},
            scouting_adjustments=[
                ScoutingAdjustment(condition="True", biases={"gateway_units": -0.5}),
            ],
            meta=MetaParams(bias_speed=1.0),
        )
        calc = BiasCalculator(profile)
        result = calc.update({"game_time_seconds": 120})
        assert result["gateway_units"] >= 0.0


class TestBiasCalculatorScoutDecay:
    def test_does_not_mutate_scout_metadata(self):
        profile = _make_profile(meta=MetaParams(scout_decay_rate=1.0))
        calc = BiasCalculator(profile)
        metadata = {"marine": {"last_seen": 100, "confidence": 1.0}}
        original_confidence = metadata["marine"]["confidence"]
        calc.update({"game_time_seconds": 100}, scout_metadata=metadata)
        assert metadata["marine"]["confidence"] == original_confidence

    def test_no_scout_metadata_uses_default_confidence(self):
        profile = _make_profile(
            initial_biases={"gateway_units": 0.5},
            scouting_adjustments=[
                ScoutingAdjustment(condition="True", biases={"gateway_units": 0.3}),
            ],
        )
        calc = BiasCalculator(profile)
        result = calc.update({"game_time_seconds": 120})
        assert result["gateway_units"] > 0.5


class TestBiasCalculatorSpeed:
    def test_low_speed_dampens_changes(self):
        profile = _make_profile(
            initial_biases={"gateway_units": 0.5},
            scouting_adjustments=[
                ScoutingAdjustment(condition="True", biases={"gateway_units": 0.5}),
            ],
            meta=MetaParams(bias_speed=0.1),
        )
        calc = BiasCalculator(profile)
        result = calc.update({"game_time_seconds": 120})
        assert result["gateway_units"] < 0.55

    def test_high_speed_applies_faster(self):
        slow = _make_profile(
            initial_biases={"gateway_units": 0.5},
            scouting_adjustments=[
                ScoutingAdjustment(condition="True", biases={"gateway_units": 0.5}),
            ],
            meta=MetaParams(bias_speed=0.1),
        )
        fast = _make_profile(
            initial_biases={"gateway_units": 0.5},
            scouting_adjustments=[
                ScoutingAdjustment(condition="True", biases={"gateway_units": 0.5}),
            ],
            meta=MetaParams(bias_speed=0.9),
        )
        c_slow = BiasCalculator(slow)
        c_fast = BiasCalculator(fast)
        f = {"game_time_seconds": 120}
        assert c_fast.update(f)["gateway_units"] > c_slow.update(f)["gateway_units"]
