import argparse
import sys

import pytest

from scripts.run import DEFAULT_MAP, DIFFICULTY_CHOICES, POLICY_MODE_CHOICES, RACE_CHOICES, _list_maps, resolve_map


def _parse_args(argv: list[str]):
    """Build a parser matching main() and parse argv."""
    parser = argparse.ArgumentParser(
        description="SC2AI — Protoss macro bot launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--realtime", action="store_true",
                        help="Run at normal speed with rendering")
    parser.add_argument("--map", default=DEFAULT_MAP)
    parser.add_argument("--surrender", action="store_true")
    parser.add_argument("--fog", action="store_true")
    parser.add_argument("--difficulty", default="Medium", choices=DIFFICULTY_CHOICES)
    parser.add_argument("--opponent-race", default="Terran", choices=RACE_CHOICES)
    parser.add_argument("--opponents", type=int, default=1, choices=range(1, 5))
    parser.add_argument("--policy-mode", default="heuristic", choices=POLICY_MODE_CHOICES)
    parser.add_argument("--experiment-id", default=None)
    parser.add_argument("--model-name", default=None)
    parser.add_argument("--model-version", default=None)
    parser.add_argument("--shadow-profile", action="append", default=None, dest="shadow_profile")
    return parser.parse_args(argv)


class FakeMaps:
    def __init__(self, result=None):
        self.result = result
        self.requested = None
        self._keys = ["AcropolisLE", "ThunderbirdLE"] if result else []

    def get(self, name):
        self.requested = name
        return self.result

    def keys(self):
        return self._keys

    def __iter__(self):
        return iter(self._keys)


def test_resolve_map_returns_configured_map():
    expected_map = object()
    fake_maps = FakeMaps(expected_map)
    fake_maps._keys = [DEFAULT_MAP]

    resolved = resolve_map(DEFAULT_MAP, fake_maps)

    assert resolved is expected_map
    assert fake_maps.requested == DEFAULT_MAP


def test_resolve_map_reports_missing_map_clearly():
    fake_maps = FakeMaps(None)

    with pytest.raises(RuntimeError) as exc_info:
        resolve_map("NonExistentMap", fake_maps)

    message = str(exc_info.value)
    assert "NonExistentMap" in message
    assert "/Applications/StarCraft II/Maps/" in message
    assert "scripts/setup_maps.sh" in message


def test_resolve_map_random_selects_map():
    fake_maps = FakeMaps(object())
    fake_maps._keys = ["AcropolisLE", "ThunderbirdLE"]

    resolved = resolve_map("random", fake_maps)

    assert resolved is not None
    assert fake_maps.requested in ("AcropolisLE", "ThunderbirdLE")


# --- Opponent config CLI tests ---

class TestDifficultyFlag:
    def test_valid_difficulty_accepted(self):
        args = _parse_args(["--difficulty", "VeryHard"])
        assert args.difficulty == "VeryHard"

    def test_invalid_difficulty_rejected(self):
        with pytest.raises(SystemExit):
            _parse_args(["--difficulty", "Impossible"])

    def test_default_difficulty_is_medium(self):
        args = _parse_args([])
        assert args.difficulty == "Medium"

    def test_cheat_difficulties_not_in_choices(self):
        for cheat in ("CheatVision", "CheatMoney", "CheatInsane"):
            assert cheat not in DIFFICULTY_CHOICES


class TestOpponentRaceFlag:
    def test_valid_race_accepted(self):
        args = _parse_args(["--opponent-race", "Zerg"])
        assert args.opponent_race == "Zerg"

    def test_invalid_race_rejected(self):
        with pytest.raises(SystemExit):
            _parse_args(["--opponent-race", "XelNaga"])

    def test_default_race_is_terran(self):
        args = _parse_args([])
        assert args.opponent_race == "Terran"

    def test_random_race_accepted(self):
        args = _parse_args(["--opponent-race", "Random"])
        assert args.opponent_race == "Random"


class TestOpponentsFlag:
    def test_valid_opponent_count_accepted(self):
        args = _parse_args(["--opponents", "3"])
        assert args.opponents == 3

    def test_default_opponents_is_one(self):
        args = _parse_args([])
        assert args.opponents == 1

    def test_zero_opponents_rejected(self):
        with pytest.raises(SystemExit):
            _parse_args(["--opponents", "0"])

    def test_five_opponents_rejected(self):
        with pytest.raises(SystemExit):
            _parse_args(["--opponents", "5"])

    def test_negative_opponents_rejected(self):
        with pytest.raises(SystemExit):
            _parse_args(["--opponents", "-1"])


class TestDefaults:
    def test_all_defaults_match_current_behavior(self):
        args = _parse_args([])
        assert args.difficulty == "Medium"
        assert args.opponent_race == "Terran"
        assert args.opponents == 1
        assert args.policy_mode == "heuristic"

    def test_combined_flags(self):
        args = _parse_args([
            "--difficulty", "Hard",
            "--opponent-race", "Protoss",
            "--opponents", "2",
        ])
        assert args.difficulty == "Hard"
        assert args.opponent_race == "Protoss"
        assert args.opponents == 2


class TestPolicyFlags:
    def test_valid_policy_mode_accepted(self):
        args = _parse_args(["--policy-mode", "ml_shadow"])
        assert args.policy_mode == "ml_shadow"

    def test_invalid_policy_mode_rejected(self):
        with pytest.raises(SystemExit):
            _parse_args(["--policy-mode", "ml"])

    def test_policy_metadata_flags_accepted(self):
        args = _parse_args([
            "--experiment-id", "ab-shadow-v1",
            "--model-name", "priority_mlp",
            "--model-version", "20260620-001",
        ])
        assert args.experiment_id == "ab-shadow-v1"
        assert args.model_name == "priority_mlp"
        assert args.model_version == "20260620-001"

    def test_shadow_profiles_accepted(self):
        args = _parse_args(["--shadow-profile", "stargate_open"])
        assert args.shadow_profile == ["stargate_open"]

    def test_multiple_shadow_profiles_accepted(self):
        args = _parse_args([
            "--shadow-profile", "stargate_open",
            "--shadow-profile", "robo_open",
            "--shadow-profile", "fast_expand",
        ])
        assert args.shadow_profile == ["stargate_open", "robo_open", "fast_expand"]
