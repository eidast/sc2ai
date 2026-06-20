from enum import Enum, auto


class BuildPhase(Enum):
    EARLY_GAME = auto()
    EXPANDING = auto()
    MID_GAME = auto()
    MAXED = auto()


PROBE_LIMIT = 70
SUPPLY_HEADROOM = 4
EXPAND_SUPPLY = 20
GATEWAY_COUNT_ONE_BASE = 1
GATEWAY_COUNT_TWO_BASE = 4
ATTACK_SUPPLY = 200

BUILD_PRIORITY = [
    "pylon",
    "gateway",
    "cybernetics_core",
    "warp_gate_research",
    "expansion",
    "gateways_extra",
]
