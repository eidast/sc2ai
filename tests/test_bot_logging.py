from src.bot.core import MyBot


def test_bot_uses_default_log_interval():
    bot = MyBot()

    assert bot.log_interval == 22


def test_bot_accepts_custom_log_interval():
    bot = MyBot(log_interval=44)

    assert bot.log_interval == 44


def test_bot_stores_opponent_difficulty():
    bot = MyBot(opponent_difficulty="VeryHard")
    assert bot.opponent_difficulty == "VeryHard"


def test_bot_stores_opponent_race():
    bot = MyBot(opponent_race="Zerg")
    assert bot.opponent_race == "Zerg"


def test_bot_stores_opponent_count():
    bot = MyBot(opponent_count=3)
    assert bot.opponent_count == 3


def test_bot_opponent_defaults():
    bot = MyBot()
    assert bot.opponent_difficulty == "Medium"
    assert bot.opponent_race == "Terran"
    assert bot.opponent_count == 1


def test_bot_policy_defaults():
    bot = MyBot()
    assert bot.policy_mode == "heuristic"
    assert bot.experiment_id is None
    assert bot.model_name is None
    assert bot.model_version is None


def test_bot_accepts_ml_shadow_policy_metadata():
    bot = MyBot(
        policy_mode="ml_shadow",
        experiment_id="ab-test-1",
        model_name="priority_mlp",
        model_version="20260620-001",
        shadow_profiles=["stargate_open"],
    )

    assert bot.policy_mode == "ml_shadow"
    assert bot.experiment_id == "ab-test-1"
    assert bot.model_name == "priority_mlp"
    assert bot.model_version == "20260620-001"


def test_bot_rejects_ml_shadow_without_shadow_profiles():
    import pytest

    with pytest.raises(ValueError, match="ml_shadow.*requires.*shadow-profile"):
        MyBot(policy_mode="ml_shadow")


def test_bot_accepts_ml_shadow_with_shadow_profiles():
    bot = MyBot(policy_mode="ml_shadow", shadow_profiles=["stargate_open"])
    assert bot.policy_mode == "ml_shadow"
    assert len(bot._shadow_profiles) == 1
    assert bot._shadow_profiles[0][0] == "stargate_open"
    assert len(bot._shadow_bias_calculators) == 1
    assert len(bot._shadow_priority_engines) == 1


def test_bot_accepts_multiple_shadow_profiles():
    bot = MyBot(
        policy_mode="ml_shadow",
        shadow_profiles=["stargate_open", "robo_open", "fast_expand"],
    )
    assert len(bot._shadow_profiles) == 3
    assert len(bot._shadow_bias_calculators) == 3
    assert len(bot._shadow_priority_engines) == 3
    names = [name for name, _ in bot._shadow_profiles]
    assert names == ["stargate_open", "robo_open", "fast_expand"]


def test_bot_ml_shadow_initializes_shadow_predictions_empty():
    bot = MyBot(policy_mode="ml_shadow", shadow_profiles=["stargate_open"])
    assert bot._last_shadow_predictions == []


def test_bot_invalid_shadow_profile_raises():
    import pytest

    with pytest.raises((FileNotFoundError, ValueError)):
        MyBot(policy_mode="ml_shadow", shadow_profiles=["nonexistent"])


def test_bot_rejects_unknown_policy_mode():
    import pytest

    with pytest.raises(ValueError, match="Unsupported policy_mode"):
        MyBot(policy_mode="ml")


def test_bot_initializes_decisions_file(tmp_path):
    bot = MyBot()

    bot._initialize_report_files(str(tmp_path), "match-1")

    assert bot._features_file == str(tmp_path / "match-1" / "features.jsonl")
    assert bot._events_file == str(tmp_path / "match-1" / "events.jsonl")
    assert bot._decisions_file == str(tmp_path / "match-1" / "decisions.jsonl")
    assert (tmp_path / "match-1" / "decisions.jsonl").exists()


def test_bot_has_worker_scout_state():
    bot = MyBot()
    assert bot._worker_scout_tag is None
    assert bot._worker_scout_active is False
    assert bot._worker_scout_waypoint_index == 0


def test_bot_computes_dynamic_max_workers():
    bot = MyBot()
    bot._last_features = {"game_time_seconds": 1000}
    bases = [
        {"ideal_mineral_workers": 16, "ideal_gas_workers": 6},
        {"ideal_mineral_workers": 16, "ideal_gas_workers": 6},
    ]
    result = bot._compute_dynamic_max_workers(bases)
    assert result == 48


def test_bot_dynamic_max_defaults_to_max_workers_early_game():
    bot = MyBot()
    bot._last_features = {"game_time_seconds": 300}
    bases = [{"ideal_mineral_workers": 16, "ideal_gas_workers": 0}]
    result = bot._compute_dynamic_max_workers(bases)
    assert result == 70


def test_bot_saturation_fallback_works():
    from types import SimpleNamespace
    from src.bot.strategy import BASE_MINERAL_RADIUS

    bot = MyBot()
    bot._last_features = None

    class FakeNexus:
        position = SimpleNamespace(x=50.0, y=50.0)
        assigned_harvesters = 12

    class FakeCollection:
        def closer_than(self, _range, _pos):
            self.amount = 8
            return self

    class FakeMinerals:
        def closer_than(self, _range, _pos):
            self.amount = 8
            return self

    class FakeGas:
        def closer_than(self, _range, _pos):
            self.amount = 0
            return self

    bot.mineral_field = FakeMinerals()
    bot.gas_buildings = FakeGas()

    ideal, current, ratio = bot._get_base_saturation(FakeNexus())
    assert ideal == 16
    assert current == 12
    assert ratio == 0.75
