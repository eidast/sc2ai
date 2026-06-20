from types import SimpleNamespace

from src.ml.observation import extract_features


class EmptyUnits:
    amount = 0

    def __bool__(self):
        return False


class UnitCollection:
    def __init__(self, amount):
        self.amount = amount

    def exclude_type(self, _unit_types):
        return self


def test_extract_features_returns_required_keys_with_empty_defaults():
    bot = SimpleNamespace(
        minerals=50,
        vespene=0,
        supply_used=12,
        supply_cap=15,
        supply_left=3,
        workers=EmptyUnits(),
        units=UnitCollection(0),
        enemy_units=[],
        time=1.5,
        townhalls=UnitCollection(1),
        state=SimpleNamespace(game_loop=33),
    )

    features = extract_features(bot)

    assert features["minerals"] == 50
    assert features["vespene"] == 0
    assert features["supply_used"] == 12
    assert features["supply_cap"] == 15
    assert features["worker_count"] == 0
    assert features["army_count"] == 0
    assert features["enemy_visible_units"] == 0
    assert features["game_time_seconds"] == 1.5
    assert features["expansion_count"] == 1
