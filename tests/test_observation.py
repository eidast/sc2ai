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

    def __iter__(self):
        return iter([])

    def __len__(self):
        return self.amount

    def closer_than(self, _distance, _position):
        return self


class MockNexus:
    def __init__(self):
        self.position = SimpleNamespace(x=50.0, y=50.0)
        self.assigned_harvesters = 12


class TownhallCollection:
    def __init__(self, amount):
        self.amount = amount
        self.ready = self
        self._nexuses = [MockNexus() for _ in range(amount)]

    def __iter__(self):
        return iter(self._nexuses)

    def __len__(self):
        return len(self._nexuses)


def test_extract_features_returns_required_keys_with_empty_defaults():
    bot = SimpleNamespace(
        minerals=50,
        vespene=0,
        supply_used=12,
        supply_cap=15,
        supply_left=3,
        workers=EmptyUnits(),
        units=UnitCollection(0),
        structures=UnitCollection(0),
        enemy_units=UnitCollection(0),
        enemy_structures=UnitCollection(0),
        mineral_field=UnitCollection(0),
        gas_buildings=UnitCollection(0),
        time=1.5,
        townhalls=TownhallCollection(1),
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
    assert features["enemy_visible_structures"] == 0
    assert features["game_time_seconds"] == 1.5
    assert features["expansion_count"] == 1
    assert features["enemy_army_composition"] == {}
    assert features["our_army_composition"] == {}
    assert features["our_structures"] == {}
    assert features["our_army_value"] == 0
    assert features["enemy_army_value"] == 0
    assert features["army_value_ratio"] == 0.0
    assert features["enemy_t3_count"] == 0
    assert features["our_t3_count"] == 0
    assert features["enemy_worker_count"] == 0
    assert isinstance(features["bases"], list)
    assert len(features["bases"]) == 1
