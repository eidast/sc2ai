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
