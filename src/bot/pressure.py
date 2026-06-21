from enum import Enum


class PressureLevel(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


def assess_pressure(
    features: dict,
    game_time: float,
    prev_level: PressureLevel = PressureLevel.NONE,
    prev_level_start: float = 0.0,
) -> tuple[PressureLevel, float]:
    signals = 0

    ratio = features.get("army_value_ratio", 1.0)
    if ratio < 0.3:
        signals += 3
    elif ratio < 0.6:
        signals += 2
    elif ratio < 0.9:
        signals += 1

    if features.get("enemy_push_active", False):
        signals += 2

    for base in features.get("bases", []):
        if base.get("enemy_nearby", 0) > 5:
            signals += 2
            break

    enemy_units = features.get("enemy_visible_units", 0)
    if enemy_units > 20:
        signals += 1
    if enemy_units > 40:
        signals += 1

    if signals >= 7:
        new_level = PressureLevel.HIGH
    elif signals >= 4:
        new_level = PressureLevel.MEDIUM
    elif signals >= 2:
        new_level = PressureLevel.LOW
    else:
        new_level = PressureLevel.NONE

    if new_level != prev_level:
        if game_time - prev_level_start < 5.0:
            return prev_level, prev_level_start
        return new_level, game_time

    return prev_level, prev_level_start


def pressure_expand_saturation(pressure: PressureLevel) -> float | None:
    _MAP = {
        PressureLevel.NONE: 0.65,
        PressureLevel.LOW: 0.75,
        PressureLevel.MEDIUM: 0.85,
        PressureLevel.HIGH: None,
    }
    return _MAP[pressure]


def pressure_expand_mineral_bank(pressure: PressureLevel) -> int | None:
    _MAP = {
        PressureLevel.NONE: 400,
        PressureLevel.LOW: 450,
        PressureLevel.MEDIUM: 600,
        PressureLevel.HIGH: None,
    }
    return _MAP[pressure]


def pressure_gateway_bonus(pressure: PressureLevel) -> int:
    _MAP = {
        PressureLevel.NONE: 0,
        PressureLevel.LOW: 1,
        PressureLevel.MEDIUM: 2,
        PressureLevel.HIGH: 3,
    }
    return _MAP[pressure]


def pressure_gateway_float_extra(pressure: PressureLevel) -> int:
    _MAP = {
        PressureLevel.NONE: 2,
        PressureLevel.LOW: 3,
        PressureLevel.MEDIUM: 4,
        PressureLevel.HIGH: 5,
    }
    return _MAP[pressure]
