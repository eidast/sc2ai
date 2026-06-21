from dataclasses import dataclass, field
from enum import Enum, auto


class ActionType(Enum):
    BUILD_UNIT = auto()
    BUILD_STRUCTURE = auto()
    RESEARCH_UPGRADE = auto()
    ECO_ACTION = auto()
    NOOP = auto()


@dataclass
class Action:
    type: ActionType = ActionType.NOOP
    target: str = ""
    score: float = 0.0
    params: dict = field(default_factory=dict)


@dataclass
class ScoutingAdjustment:
    condition: str
    biases: dict[str, float]


@dataclass
class MetaParams:
    bias_speed: float = 0.3
    scout_decay_rate: float = 0.05
    max_workers: int = 70
    target_bases: int = 4


@dataclass
class FormulaEntry:
    formula: str
    requires: list[str] = field(default_factory=list)


@dataclass
class StrategyProfile:
    name: str
    race: str
    initial_biases: dict[str, float] = field(default_factory=dict)
    scouting_adjustments: list[ScoutingAdjustment] = field(default_factory=list)
    priority_formulas: dict[str, FormulaEntry] = field(default_factory=dict)
    meta: MetaParams = field(default_factory=MetaParams)
    description: str = ""
