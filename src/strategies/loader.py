import logging
from pathlib import Path

from src.strategies.types import (
    StrategyProfile,
    ScoutingAdjustment,
    MetaParams,
    FormulaEntry,
)
from src.strategies.schema import validate, ValidationError as SchemaValidationError

logger = logging.getLogger(__name__)


class StrategyLoader:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir).resolve()
        self._cache: dict[str, StrategyProfile] = {}

    def load(self, path: str | Path) -> StrategyProfile:
        full_path = Path(path)
        if not full_path.is_absolute():
            full_path = self.base_dir / full_path

        raw = self._read_yaml(full_path)

        errors = validate(raw)
        if errors:
            msg = f"Validation failed for {full_path}: {'; '.join(errors)}"
            logger.error(msg)
            raise SchemaValidationError(msg)

        return self._parse(raw)

    def load_all(self, race: str) -> list[StrategyProfile]:
        race_dir = self.base_dir / race.lower()
        if not race_dir.is_dir():
            logger.warning("No strategy directory for race: %s", race)
            return []

        profiles = []
        for yaml_file in sorted(race_dir.glob("*.yaml")):
            try:
                profile = self.load(yaml_file)
                self._cache[profile.name] = profile
                profiles.append(profile)
            except (SchemaValidationError, ValueError) as e:
                logger.warning("Skipping invalid profile %s: %s", yaml_file, e)

        return profiles

    def get_default(self, race: str) -> StrategyProfile:
        cache_key = f"{race}:default"
        if cache_key in self._cache:
            return self._cache[cache_key]

        profiles = self.load_all(race)
        for profile in profiles:
            if profile.name == "standard_macro":
                self._cache[cache_key] = profile
                return profile

        if profiles:
            self._cache[cache_key] = profiles[0]
            return profiles[0]

        raise FileNotFoundError(f"No profiles found for race: {race}")

    @staticmethod
    def _read_yaml(path: Path) -> dict:
        import yaml
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError(f"YAML file {path} must contain a mapping, got {type(data).__name__}")
        return data

    @staticmethod
    def _parse(raw: dict) -> StrategyProfile:
        adjustments = []
        for adj_data in raw.get("scouting_adjustments", []):
            adjustments.append(ScoutingAdjustment(
                condition=adj_data["condition"],
                biases=adj_data["biases"],
            ))

        meta_raw = raw.get("meta", {}) or {}
        meta = MetaParams(
            bias_speed=float(meta_raw.get("bias_speed", 0.3)),
            scout_decay_rate=float(meta_raw.get("scout_decay_rate", 0.05)),
            max_workers=int(meta_raw.get("max_workers", 70)),
            target_bases=int(meta_raw.get("target_bases", 4)),
        )

        formulas: dict[str, FormulaEntry] = {}
        for key, value in raw.get("priority_formulas", {}).items():
            if isinstance(value, str):
                formulas[key] = FormulaEntry(formula=value)
            elif isinstance(value, dict):
                formulas[key] = FormulaEntry(
                    formula=value["formula"],
                    requires=value.get("requires", []),
                )

        return StrategyProfile(
            name=raw.get("name", "unnamed"),
            race=raw.get("race", "Protoss"),
            initial_biases=raw.get("initial_biases", {}),
            scouting_adjustments=adjustments,
            priority_formulas=formulas,
            meta=meta,
            description=raw.get("description", ""),
        )
