from pathlib import Path
import pytest
from src.strategies.loader import StrategyLoader
from src.strategies.schema import ValidationError


_DATA_DIR = Path(__file__).parent.parent / "src" / "data" / "strategies"


class TestStrategyLoader:
    def test_load_valid_profile(self):
        loader = StrategyLoader(_DATA_DIR)
        profile = loader.load("protoss/standard_macro.yaml")
        assert profile.name == "standard_macro"
        assert profile.race == "Protoss"
        assert "gateway_units" in profile.initial_biases
        assert len(profile.priority_formulas) > 0
        assert profile.meta.bias_speed == 0.3

    def test_load_all_for_protoss(self):
        loader = StrategyLoader(_DATA_DIR)
        profiles = loader.load_all("protoss")
        assert len(profiles) >= 4
        names = {p.name for p in profiles}
        assert "standard_macro" in names
        assert "stargate_open" in names
        assert "robo_open" in names
        assert "fast_expand" in names

    def test_load_all_nonexistent_race(self):
        loader = StrategyLoader(_DATA_DIR)
        profiles = loader.load_all("zerg")
        assert len(profiles) == 0

    def test_get_default_returns_standard_macro(self):
        loader = StrategyLoader(_DATA_DIR)
        profile = loader.get_default("protoss")
        assert profile.name == "standard_macro"

    def test_all_profiles_in_dir_are_valid(self):
        loader = StrategyLoader(_DATA_DIR)
        protoss_dir = _DATA_DIR / "protoss"
        yaml_files = sorted(protoss_dir.glob("*.yaml"))
        assert len(yaml_files) > 0
        for yf in yaml_files:
            profile = loader.load(yf)
            assert profile.name
            assert profile.race == "Protoss"

    def test_profile_has_required_fields(self):
        loader = StrategyLoader(_DATA_DIR)
        profile = loader.load("protoss/standard_macro.yaml")
        assert profile.name
        assert profile.race
        assert isinstance(profile.initial_biases, dict)
        assert isinstance(profile.priority_formulas, dict)

    def test_invalid_bias_value_raises(self):
        fake_dir = Path("/tmp/nonexistent_strategy_dir")
        with pytest.raises(FileNotFoundError):
            loader = StrategyLoader(fake_dir)
            loader.load("nonexistent.yaml")
