from enum import Enum, auto
from dataclasses import dataclass, field
import math
from typing import Any


class ScoutState(Enum):
    IDLE = auto()
    EXPLORING = auto()
    RETREATING = auto()
    DEAD = auto()


@dataclass
class ScoutIntel:
    enemy_base_found: bool = False
    enemy_race_confirmed: str | None = None
    enemy_structures_seen: list[str] = field(default_factory=list)
    last_scout_time: float = 0.0


class ScoutMetadata:
    def __init__(self, decay_rate: float = 0.05):
        self._units: dict[str, dict] = {}
        self._decay_rate = decay_rate

    def observe(self, unit_type_name: str, game_time: float) -> None:
        self._units[unit_type_name] = {
            "last_seen": game_time,
            "confidence": 1.0,
        }

    def apply_decay(self, current_time: float) -> None:
        for unit_data in self._units.values():
            delta = current_time - unit_data["last_seen"]
            if delta > 0:
                unit_data["confidence"] = math.exp(-self._decay_rate * delta)

    def to_dict(self) -> dict[str, dict]:
        return dict(self._units)

    def clear(self) -> None:
        self._units.clear()


def get_scout_waypoints(
    enemy_start_locations: list[Any],
    expansions: list[Any] | None = None,
) -> list[tuple[float, float]]:
    waypoints: list[tuple[float, float]] = []
    for loc in enemy_start_locations:
        waypoints.append((float(loc.x), float(loc.y)))
    if expansions:
        for exp in expansions:
            waypoints.append((float(exp.x), float(exp.y)))
    return waypoints


def update_scout_waypoints(
    current: list[tuple[float, float]],
    expansions: list[Any],
) -> list[tuple[float, float]]:
    result = list(current)
    for exp in expansions:
        pt = (float(exp.x), float(exp.y))
        if pt not in result:
            result.append(pt)
    return result


def should_retreat_scout(
    scout: Any,
    enemy_units: list[Any],
    retreat_hp_ratio: float = 0.5,
    threat_range: float = 8.0,
) -> bool:
    if not enemy_units:
        return False
    hp = getattr(scout, "health", 0)
    max_hp = getattr(scout, "health_max", 1)
    shields = getattr(scout, "shield", 0)
    max_shields = getattr(scout, "shield_max", 0)
    total_hp = hp + shields
    total_max = max_hp + max_shields
    if total_max == 0:
        return False
    hp_ratio = total_hp / total_max
    if hp_ratio > retreat_hp_ratio:
        return False
    scout_pos = scout.position
    for enemy in enemy_units:
        enemy_pos = getattr(enemy, "position", None)
        if enemy_pos is None:
            continue
        dx = scout_pos.x - enemy_pos.x
        dy = scout_pos.y - enemy_pos.y
        dist = (dx * dx + dy * dy) ** 0.5
        if dist <= threat_range:
            return True
    return False


def compute_next_scout_move(
    scout: Any,
    waypoints: list[tuple[float, float]],
    current_index: int,
    proximity: float = 3.0,
) -> tuple[float, float] | None:
    if current_index >= len(waypoints):
        return None
    wx, wy = waypoints[current_index]
    sx = scout.position.x
    sy = scout.position.y
    dist = ((sx - wx) ** 2 + (sy - wy) ** 2) ** 0.5
    if dist <= proximity:
        current_index += 1
        if current_index >= len(waypoints):
            return None
        wx, wy = waypoints[current_index]
    return (wx, wy)
