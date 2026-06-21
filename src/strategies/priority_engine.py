"""Priority engine — evaluates utility of reachable actions and selects the best."""

import logging

from src.strategies.types import Action, ActionType, StrategyProfile
from src.strategies.formula import evaluate_formula, prepare_builtins

logger = logging.getLogger(__name__)

_BUILD_UNIT_TARGETS = {
    "STALKER", "ZEALOT", "SENTRY", "ADEPT", "HIGHTEMPLAR", "DARKTEMPLAR",
    "ARCHON", "IMMORTAL", "COLOSSUS", "DISRUPTOR", "OBSERVER", "WARPPRISM",
    "PHOENIX", "VOIDRAY", "ORACLE", "CARRIER", "TEMPEST",
}

_BUILD_STRUCTURE_TARGETS = {
    "PYLON", "GATEWAY", "CYBERNETICSCORE", "STARGATE", "ROBOTICSFACILITY",
    "TWILIGHTCOUNCIL", "FORGE", "NEXUS", "ASSIMILATOR",
}

_RESEARCH_UPGRADE_TARGETS = {
    "WARPGATERESEARCH", "BLINKTECH", "CHARGE",
    "PROTOSSGROUNDWEAPONSLEVEL1", "PROTOSSGROUNDWEAPONSLEVEL2", "PROTOSSGROUNDWEAPONSLEVEL3",
    "PROTOSSGROUNDARMORLEVEL1", "PROTOSSGROUNDARMORLEVEL2", "PROTOSSGROUNDARMORLEVEL3",
    "PROTOSSSHIELDSLEVEL1", "PROTOSSSHIELDSLEVEL2", "PROTOSSSHIELDSLEVEL3",
}

_ECO_ACTION_TARGETS = {"PROBE"}

_ACTION_CATEGORIES = {
    ActionType.BUILD_UNIT: _BUILD_UNIT_TARGETS,
    ActionType.BUILD_STRUCTURE: _BUILD_STRUCTURE_TARGETS,
    ActionType.RESEARCH_UPGRADE: _RESEARCH_UPGRADE_TARGETS,
    ActionType.ECO_ACTION: _ECO_ACTION_TARGETS,
}


class PriorityEngine:
    def __init__(self, profile: StrategyProfile):
        self._profile = profile
        self._formulas: dict[str, str] = {
            k: v.formula for k, v in profile.priority_formulas.items()
        }
        self._requires: dict[str, list[str]] = {
            k: v.requires for k, v in profile.priority_formulas.items()
        }

    def evaluate(
        self,
        bias_vector: dict[str, float],
        features: dict,
        *,
        own_composition: dict[str, int] | None = None,
        structures: dict[str, int] | None = None,
        completed_upgrades: set[str] | None = None,
        prev_action: Action | None = None,
    ) -> Action:
        builtins = prepare_builtins(
            features,
            own_composition=own_composition,
            structures=structures,
            completed_upgrades=completed_upgrades,
        )

        best_action = Action(type=ActionType.NOOP, target="", score=-1.0)
        candidates = self._get_formula_actions()

        for target, action_type in candidates:
            entry_requires = self._requires.get(target)
            if not self._is_reachable(target, action_type, features, structures, completed_upgrades, requires=entry_requires):
                continue

            formula = self._formulas.get(target)
            if not formula:
                continue

            score = evaluate_formula(formula, bias_vector, builtins)

            if prev_action and prev_action.type != ActionType.NOOP:
                if action_type == prev_action.type and target == prev_action.target:
                    score *= 1.15

            if score > best_action.score:
                best_action = Action(type=action_type, target=target, score=score)
            elif score == best_action.score and best_action.score >= 0:
                if target < best_action.target:
                    best_action = Action(type=action_type, target=target, score=score)

        if best_action.score < 0:
            return Action(type=ActionType.NOOP, target="", score=0.0)

        return best_action

    def _get_formula_actions(self) -> list[tuple[str, ActionType]]:
        candidates = []
        for target in self._formulas:
            action_type = self._classify_target(target)
            if action_type:
                candidates.append((target, action_type))
        return candidates

    @staticmethod
    def _classify_target(target: str) -> ActionType | None:
        if target in _BUILD_UNIT_TARGETS:
            return ActionType.BUILD_UNIT
        if target in _BUILD_STRUCTURE_TARGETS:
            return ActionType.BUILD_STRUCTURE
        if target in _RESEARCH_UPGRADE_TARGETS:
            return ActionType.RESEARCH_UPGRADE
        if target in _ECO_ACTION_TARGETS:
            return ActionType.ECO_ACTION
        return None

    @staticmethod
    def _is_reachable(
        target: str,
        action_type: ActionType,
        features: dict,
        structures: dict[str, int] | None,
        completed_upgrades: set[str] | None,
        requires: list[str] | None = None,
    ) -> bool:
        supply_left = features.get("supply_left", 0)
        minerals = features.get("minerals", 0)
        vespene = features.get("vespene", 0)

        if action_type == ActionType.BUILD_UNIT and supply_left < 1:
            return False

        if minerals <= 0 and action_type != ActionType.NOOP:
            return False

        if requires and structures is not None:
            for req in requires:
                if structures.get(req, 0) <= 0:
                    return False

        return True
