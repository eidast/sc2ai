from enum import Enum, auto


class BuildPhase(Enum):
    EARLY_GAME = auto()
    EXPANDING = auto()
    MID_GAME = auto()
    MAXED = auto()


class CameraMode(Enum):
    SCOUT = auto()
    EXPAND = auto()
    DEFEND = auto()
    ARMY = auto()
    ENGAGE = auto()


WORKERS_PER_MINERAL = 2
WORKERS_PER_GAS = 3
MAX_SATURATION_RATIO = 0.9
THREAT_RANGE = 15
ENGAGE_RANGE = 8
BASE_MINERAL_RADIUS = 10
