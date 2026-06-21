from enum import Enum, auto
from dataclasses import dataclass


class DecisionState(Enum):
    DEFEND = auto()
    ATTACK = auto()
    RECOVER = auto()
    SURRENDER = auto()
    WON = auto()


@dataclass
class Decision:
    state: DecisionState
    reason: str


RACE_MULTIPLIERS = {
    "Zerg": 0.85,
    "Terran": 1.0,
    "Protoss": 1.1,
}

FOG_MULTIPLIER = 1.3

SUPPLY_CAP_THRESHOLD = 200

SURRENDER_MIN_TIME = 300.0
SURRENDER_ARMY_VALUE_RATIO = 0.15
SURRENDER_WORKER_MIN = 10
SURRENDER_SUSTAIN_SECONDS = 120.0
SURRENDER_FOG_ARMY_VALUE_RATIO = 0.10

VICTORY_MIN_TIME = 120.0
VICTORY_ENEMY_GONE_SECONDS = 60.0
VICTORY_MIN_ARMY = 5

RECOVER_ARMY_VALUE_RATIO = 0.6
RECOVER_WORKER_MIN = 20

ATTACK_TIMEOUT_SECONDS = 120.0

ATTACK_PHASES = [
    {"name": "early",  "max_time": 240.0, "min_supply": 30,  "army_value_ratio": 1.5},
    {"name": "mid",    "max_time": 600.0, "min_supply": 80,  "army_value_ratio": 1.2},
    {"name": "late",   "max_time": 900.0, "min_supply": 100, "army_value_ratio": 1.2},
    {"name": "desperate", "max_time": float("inf"), "min_supply": 60, "army_value_ratio": 0.0},
]


def _get_game_phase(game_time: float) -> dict:
    for phase in ATTACK_PHASES:
        if game_time < phase["max_time"]:
            return phase
    return ATTACK_PHASES[-1]


def _get_race_multiplier(enemy_race_name: str | None) -> float:
    race = enemy_race_name.title() if enemy_race_name else "Terran"
    return RACE_MULTIPLIERS.get(race, 1.0)


def _compute_supply_min(phase: dict, race_mult: float, fog_enabled: bool) -> float:
    base = phase["min_supply"] * race_mult
    if fog_enabled:
        base *= FOG_MULTIPLIER
    return base


def _surrender_conditions_met(features: dict, fog_enabled: bool) -> bool:
    game_time = features.get("game_time_seconds", 0)
    threshold = SURRENDER_FOG_ARMY_VALUE_RATIO if fog_enabled else SURRENDER_ARMY_VALUE_RATIO
    army_value_ratio = features.get("army_value_ratio", 0.0)
    worker_count = features.get("worker_count", 0)

    if game_time < SURRENDER_MIN_TIME:
        return False
    if army_value_ratio >= threshold:
        return False
    if worker_count >= SURRENDER_WORKER_MIN:
        return False
    return True


def evaluate_decision(
    features: dict,
    current_state: DecisionState,
    enemy_race_name: str | None,
    fog_enabled: bool = False,
    surrender_enabled: bool = False,
    time_in_state: float = 0.0,
    surrender_sustained: float = 0.0,
    enemy_gone_sustained: float = 0.0,
    enemy_push_active: bool = False,
) -> Decision:
    game_time = features.get("game_time_seconds", 0)
    supply_used = features.get("supply_used", 0)
    army_count = features.get("army_count", 0)
    army_value_ratio = features.get("army_value_ratio", 0.0)
    our_t3_count = features.get("our_t3_count", 0)
    enemy_t3_count = features.get("enemy_t3_count", 0)
    worker_count = features.get("worker_count", 0)
    enemy_visible_structures = features.get("enemy_visible_structures", 0)

    if current_state == DecisionState.SURRENDER:
        return Decision(DecisionState.SURRENDER, "already surrendered")

    if current_state == DecisionState.WON:
        return Decision(DecisionState.WON, "already won")

    if game_time >= VICTORY_MIN_TIME and army_count >= VICTORY_MIN_ARMY and enemy_visible_structures == 0:
        if enemy_gone_sustained >= VICTORY_ENEMY_GONE_SECONDS:
            return Decision(DecisionState.WON, "enemy eliminated — victory")

    if surrender_enabled and current_state != DecisionState.ATTACK:
        if _surrender_conditions_met(features, fog_enabled):
            if surrender_sustained >= SURRENDER_SUSTAIN_SECONDS:
                return Decision(DecisionState.SURRENDER, "no comeback possible")

    phase = _get_game_phase(game_time)
    race_mult = _get_race_multiplier(enemy_race_name)
    supply_min = _compute_supply_min(phase, race_mult, fog_enabled)

    if current_state == DecisionState.DEFEND:
        if supply_used >= SUPPLY_CAP_THRESHOLD:
            return Decision(DecisionState.ATTACK, "supply cap reached")

        if enemy_push_active and supply_used >= supply_min * 0.4:
            return Decision(DecisionState.ATTACK, "enemy push — counter-attack")

        if enemy_t3_count > 0 and our_t3_count == 0 and game_time > 360 and army_count >= 12:
            return Decision(DecisionState.ATTACK, "T3 window — attack before enemy outscales")

        phase_ratio = phase["army_value_ratio"]
        if (
            game_time >= 60
            and army_value_ratio >= phase_ratio
            and supply_used >= supply_min
            and phase["name"] != "desperate"
        ):
            return Decision(DecisionState.ATTACK, f"army advantage ({phase['name']})")

        if phase["name"] == "desperate" and supply_used >= supply_min:
            return Decision(DecisionState.ATTACK, "desperate phase — all-in")

        if time_in_state >= 60 and army_count >= 8 and army_value_ratio > 0.8:
            return Decision(DecisionState.ATTACK, "hoard timeout — attack")

        return Decision(DecisionState.DEFEND, "no attack condition met")

    if current_state == DecisionState.ATTACK:
        if army_count < 3:
            return Decision(DecisionState.RECOVER, "army destroyed")

        if time_in_state >= ATTACK_TIMEOUT_SECONDS:
            return Decision(DecisionState.RECOVER, "attack timeout")

        return Decision(DecisionState.ATTACK, "attacking")

    if current_state == DecisionState.RECOVER:
        if army_value_ratio >= RECOVER_ARMY_VALUE_RATIO and worker_count >= RECOVER_WORKER_MIN:
            return Decision(DecisionState.DEFEND, "army and eco recovered")

        return Decision(DecisionState.RECOVER, "rebuilding")

    return Decision(DecisionState.DEFEND, "default")
