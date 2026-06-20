import math
import pytest
from src.bot.scout import ScoutMetadata


class TestScoutMetadata:
    def test_observe_records_unit_type(self):
        sm = ScoutMetadata()
        sm.observe("MARINE", 60.0)
        data = sm.to_dict()
        assert "MARINE" in data
        assert data["MARINE"]["last_seen"] == 60.0
        assert data["MARINE"]["confidence"] == 1.0

    def test_decay_reduces_confidence(self):
        sm = ScoutMetadata(decay_rate=0.1)
        sm.observe("MARINE", 100.0)
        sm.apply_decay(110.0)
        data = sm.to_dict()
        assert data["MARINE"]["confidence"] < 1.0
        expected = math.exp(-0.1 * 10)
        assert data["MARINE"]["confidence"] == pytest.approx(expected)

    def test_reobservation_resets_confidence(self):
        sm = ScoutMetadata(decay_rate=0.1)
        sm.observe("MARINE", 100.0)
        sm.apply_decay(110.0)
        sm.observe("MARINE", 120.0)
        data = sm.to_dict()
        assert data["MARINE"]["confidence"] == 1.0
        assert data["MARINE"]["last_seen"] == 120.0

    def test_clear_removes_all_data(self):
        sm = ScoutMetadata()
        sm.observe("MARINE", 60.0)
        sm.observe("TANK", 70.0)
        sm.clear()
        assert sm.to_dict() == {}

    def test_multiple_unit_types(self):
        sm = ScoutMetadata()
        sm.observe("MARINE", 60.0)
        sm.observe("TANK", 65.0)
        sm.apply_decay(70.0)
        data = sm.to_dict()
        assert "MARINE" in data
        assert "TANK" in data
        assert data["MARINE"]["confidence"] != 1.0
        assert data["TANK"]["confidence"] != 1.0
        assert data["TANK"]["confidence"] > data["MARINE"]["confidence"]
