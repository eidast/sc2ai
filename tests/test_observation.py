from types import SimpleNamespace

from src.ml.observation import extract_features


class EmptyUnits:
    amount = 0

    def __bool__(self):
        return False

    def __iter__(self):
        return iter([])

    def closer_than(self, _distance, _position):
        return self

    @property
    def idle(self):
        return self


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

    @property
    def ready(self):
        return self


class MockNexus:
    def __init__(self, tag=1):
        self.position = SimpleNamespace(x=50.0, y=50.0)
        self.assigned_harvesters = 12
        self.tag = tag


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
    assert features["collected_minerals"] == 0
    assert features["collected_vespene"] == 0
    assert isinstance(features["bases"], list)
    assert len(features["bases"]) == 1


def test_extract_features_includes_collected_resources_from_score():
    score = SimpleNamespace(collected_minerals=15000, collected_vespene=4200)
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
        time=120.0,
        townhalls=TownhallCollection(1),
        state=SimpleNamespace(game_loop=33, score=score),
    )

    features = extract_features(bot)

    assert features["collected_minerals"] == 15000
    assert features["collected_vespene"] == 4200
    assert isinstance(features["collected_minerals"], int)
    assert isinstance(features["collected_vespene"], int)


def test_extract_base_features_includes_enriched_fields():
    score = SimpleNamespace(collected_minerals=0, collected_vespene=0)
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
        time=120.0,
        townhalls=TownhallCollection(1),
        state=SimpleNamespace(game_loop=33, score=score),
    )

    features = extract_features(bot)
    bases = features["bases"]
    assert len(bases) == 1
    base = bases[0]

    assert "mineral_patches" in base
    assert "gas_geysers" in base
    assert "ideal_mineral_workers" in base
    assert "ideal_gas_workers" in base
    assert "actual_mineral_workers" in base
    assert "actual_gas_workers" in base
    assert "idle_workers_nearby" in base
    assert "mineral_saturation" in base
    assert "gas_saturation" in base
    assert "total_saturation" in base
    assert "status" in base

    assert "ideal_workers" in base
    assert "current_workers" in base
    assert "saturation_ratio" in base
    assert "army_nearby" in base
    assert "enemy_nearby" in base


def test_base_saturation_status_classification():
    from src.ml.observation import _extract_base_features

    class WorkerUnits:
        amount = 0
        idle = property(lambda self: self)
        gathering = property(lambda self: self)

        def __iter__(self):
            return iter([])

        def __bool__(self):
            return False

        def closer_than(self, *args):
            return self

        @property
        def first(self):
            return None

    class GasBuildings:
        amount = 0
        ready = property(lambda self: self)

        def __iter__(self):
            return iter([])

        def closer_than(self, *args):
            return self

    score = SimpleNamespace(collected_minerals=0, collected_vespene=0)
    bot = SimpleNamespace(
        mineral_field=UnitCollection(8),
        gas_buildings=GasBuildings(),
        units=UnitCollection(0),
        structures=UnitCollection(0),
        enemy_units=UnitCollection(0),
        workers=WorkerUnits(),
        townhalls=TownhallCollection(1),
        time=120.0,
        state=SimpleNamespace(game_loop=33, score=score),
    )

    bases = _extract_base_features(bot)
    assert len(bases) == 1
    assert bases[0]["ideal_mineral_workers"] == 16
    assert bases[0]["status"] == "optimal"
    assert bases[0]["mineral_saturation"] == 0.75
