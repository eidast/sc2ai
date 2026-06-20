"""Bias calculator — converts scouting + metrics into continuous bias vector."""

import logging
import math

from src.strategies.types import StrategyProfile, ScoutingAdjustment
from src.strategies.formula import evaluate_condition

logger = logging.getLogger(__name__)


class BiasCalculator:
    def __init__(self, profile: StrategyProfile):
        self._profile = profile
        self._biases: dict[str, float] = dict(profile.initial_biases)
        self._initialized = False
        self._game_time: float = 0.0

    @property
    def bias_vector(self) -> dict[str, float]:
        return dict(self._biases)

    def update(
        self,
        features: dict,
        scout_metadata: dict[str, dict] | None = None,
    ) -> dict[str, float]:
        if not self._initialized:
            self._biases = dict(self._profile.initial_biases)
            self._initialized = True

        self._game_time = float(features.get("game_time_seconds", 0))

        if scout_metadata:
            self._apply_scout_decay(scout_metadata)

        for adj in self._profile.scouting_adjustments:
            confidence = self._get_adjustment_confidence(adj, features, scout_metadata)
            if confidence <= 0:
                continue

            if evaluate_condition(adj.condition, features):
                self._apply_adjustment(adj, confidence)

        for key in self._biases:
            self._biases[key] = max(0.0, min(1.0, self._biases[key]))

        return dict(self._biases)

    def _apply_scout_decay(self, metadata: dict[str, dict]) -> None:
        decay_rate = self._profile.meta.scout_decay_rate
        for unit_data in metadata.values():
            if isinstance(unit_data, dict) and "confidence" in unit_data:
                unit_data["confidence"] *= math.exp(-decay_rate)

    def _get_adjustment_confidence(
        self,
        adj: ScoutingAdjustment,
        features: dict,
        scout_metadata: dict[str, dict] | None,
    ) -> float:
        if not scout_metadata:
            return 0.5

        total_confidence = 0.0
        count = 0
        for value in scout_metadata.values():
            if isinstance(value, dict) and "confidence" in value:
                total_confidence += float(value["confidence"])
                count += 1

        if count == 0:
            return 0.5

        return total_confidence / count

    def _apply_adjustment(self, adj: ScoutingAdjustment, confidence: float) -> None:
        speed = self._profile.meta.bias_speed

        for key, delta in adj.biases.items():
            current = self._biases.get(key, 0.0)
            effective = delta * speed * confidence
            target = current + effective
            new_value = self._ema(current, target, speed)
            self._biases[key] = max(0.0, min(1.0, new_value))

    @staticmethod
    def _ema(current: float, target: float, alpha: float) -> float:
        return current + alpha * (target - current)
