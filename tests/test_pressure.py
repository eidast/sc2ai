from src.bot.pressure import (
    PressureLevel,
    assess_pressure,
    pressure_expand_saturation,
    pressure_expand_mineral_bank,
    pressure_gateway_bonus,
    pressure_gateway_float_extra,
)


def _make_features(**overrides):
    return {
        "army_value_ratio": overrides.get("army_value_ratio", 1.0),
        "enemy_push_active": overrides.get("enemy_push_active", False),
        "enemy_visible_units": overrides.get("enemy_visible_units", 0),
        "bases": overrides.get("bases", []),
        "game_time_seconds": overrides.get("game_time_seconds", 0),
    }


class TestAssessPressure:
    def test_no_pressure_when_safe(self):
        features = _make_features(army_value_ratio=2.0, enemy_visible_units=5)
        level, _ = assess_pressure(features, 10.0)
        assert level == PressureLevel.NONE

    def test_low_pressure_when_slightly_behind(self):
        features = _make_features(army_value_ratio=0.5)
        level, _ = assess_pressure(features, 10.0)
        assert level == PressureLevel.LOW

    def test_none_pressure_when_ratio_above_06(self):
        features = _make_features(army_value_ratio=0.7)
        level, _ = assess_pressure(features, 10.0)
        assert level == PressureLevel.NONE

    def test_medium_pressure_with_enemy_push(self):
        features = _make_features(
            army_value_ratio=0.4,
            enemy_push_active=True,
            bases=[{"enemy_nearby": 10}],
        )
        level, _ = assess_pressure(features, 10.0)
        assert level == PressureLevel.MEDIUM

    def test_high_pressure_when_overwhelmed(self):
        features = _make_features(
            army_value_ratio=0.1,
            enemy_push_active=True,
            enemy_visible_units=45,
            bases=[{"enemy_nearby": 10}],
        )
        level, _ = assess_pressure(features, 10.0)
        assert level == PressureLevel.HIGH

    def test_low_pressure_from_enemy_push_alone(self):
        features = _make_features(army_value_ratio=1.5, enemy_push_active=True)
        level, _ = assess_pressure(features, 10.0)
        assert level == PressureLevel.LOW

    def test_medium_from_enemy_push_and_ratio(self):
        features = _make_features(
            army_value_ratio=0.5,
            enemy_push_active=True,
        )
        level, _ = assess_pressure(features, 10.0)
        assert level == PressureLevel.MEDIUM

    def test_hysteresis_prevents_rapid_change(self):
        features_low = _make_features(army_value_ratio=0.5)
        features_med = _make_features(army_value_ratio=0.4, enemy_push_active=True)

        level, start = assess_pressure(features_low, 10.0)
        assert level == PressureLevel.LOW

        level, start = assess_pressure(features_med, 12.0, level, start)
        assert level == PressureLevel.LOW

    def test_hysteresis_allows_sustained_change(self):
        features_med = _make_features(army_value_ratio=0.4, enemy_push_active=True)

        level, start = assess_pressure(features_med, 10.0)
        assert level == PressureLevel.MEDIUM

        level, _ = assess_pressure(features_med, 16.0, level, start)
        assert level == PressureLevel.MEDIUM

    def test_edge_case_all_signals_maximum(self):
        features = _make_features(
            army_value_ratio=0.0,
            enemy_push_active=True,
            enemy_visible_units=100,
            bases=[{"enemy_nearby": 20}],
        )
        level, _ = assess_pressure(features, 10.0)
        assert level == PressureLevel.HIGH

    def test_edge_case_empty_bases(self):
        features = _make_features(army_value_ratio=0.5, bases=[])
        level, _ = assess_pressure(features, 10.0)
        assert level == PressureLevel.LOW


class TestPressureThresholds:
    def test_expand_saturation_none(self):
        assert pressure_expand_saturation(PressureLevel.NONE) == 0.65

    def test_expand_saturation_low(self):
        assert pressure_expand_saturation(PressureLevel.LOW) == 0.75

    def test_expand_saturation_medium(self):
        assert pressure_expand_saturation(PressureLevel.MEDIUM) == 0.85

    def test_expand_saturation_high_is_none(self):
        assert pressure_expand_saturation(PressureLevel.HIGH) is None

    def test_expand_mineral_bank_none(self):
        assert pressure_expand_mineral_bank(PressureLevel.NONE) == 400

    def test_expand_mineral_bank_low(self):
        assert pressure_expand_mineral_bank(PressureLevel.LOW) == 450

    def test_expand_mineral_bank_medium(self):
        assert pressure_expand_mineral_bank(PressureLevel.MEDIUM) == 600

    def test_expand_mineral_bank_high_is_none(self):
        assert pressure_expand_mineral_bank(PressureLevel.HIGH) is None

    def test_gateway_bonus_none(self):
        assert pressure_gateway_bonus(PressureLevel.NONE) == 0

    def test_gateway_bonus_low(self):
        assert pressure_gateway_bonus(PressureLevel.LOW) == 1

    def test_gateway_bonus_medium(self):
        assert pressure_gateway_bonus(PressureLevel.MEDIUM) == 2

    def test_gateway_bonus_high(self):
        assert pressure_gateway_bonus(PressureLevel.HIGH) == 3

    def test_gateway_float_extra_none(self):
        assert pressure_gateway_float_extra(PressureLevel.NONE) == 2

    def test_gateway_float_extra_low(self):
        assert pressure_gateway_float_extra(PressureLevel.LOW) == 3

    def test_gateway_float_extra_medium(self):
        assert pressure_gateway_float_extra(PressureLevel.MEDIUM) == 4

    def test_gateway_float_extra_high(self):
        assert pressure_gateway_float_extra(PressureLevel.HIGH) == 5
