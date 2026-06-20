from src.ml.report import _build_event_ranges, _build_timeline_data, _compute_metrics


class TestBuildEventRanges:
    def test_empty_input(self):
        assert _build_event_ranges([]) == []

    def test_single_event(self):
        events = [{"time": 10.0, "type": "supply_block", "severity": "high"}]
        ranges = _build_event_ranges(events)
        assert len(ranges) == 1
        assert ranges[0]["type"] == "supply_block"
        assert ranges[0]["severity"] == "high"
        assert ranges[0]["count"] == 1
        assert ranges[0]["first"] == 10.0
        assert ranges[0]["last"] == 10.0
        assert ranges[0]["duration"] == 0.0

    def test_consecutive_same_type_merged(self):
        events = [
            {"time": 120.0, "type": "supply_block", "severity": "high"},
            {"time": 120.2, "type": "supply_block", "severity": "high"},
            {"time": 120.4, "type": "supply_block", "severity": "high"},
        ]
        ranges = _build_event_ranges(events)
        assert len(ranges) == 1
        assert ranges[0]["type"] == "supply_block"
        assert ranges[0]["count"] == 3
        assert ranges[0]["first"] == 120.0
        assert ranges[0]["last"] == 120.4
        assert ranges[0]["duration"] == 0.4

    def test_different_types_not_merged(self):
        events = [
            {"time": 100.0, "type": "resource_float", "severity": "medium"},
            {"time": 100.2, "type": "supply_block", "severity": "high"},
            {"time": 100.4, "type": "resource_float", "severity": "medium"},
        ]
        ranges = _build_event_ranges(events)
        assert len(ranges) == 2
        types = sorted(r["type"] for r in ranges)
        assert types == ["resource_float", "supply_block"]
        rf = [r for r in ranges if r["type"] == "resource_float"][0]
        assert rf["count"] == 2

    def test_interrupted_sequences_merged_by_type(self):
        events = [
            {"time": 50.0, "type": "resource_float", "severity": "medium"},
            {"time": 50.2, "type": "resource_float", "severity": "medium"},
            {"time": 60.0, "type": "supply_block", "severity": "high"},
            {"time": 80.0, "type": "resource_float", "severity": "medium"},
            {"time": 80.2, "type": "resource_float", "severity": "medium"},
        ]
        ranges = _build_event_ranges(events)
        assert len(ranges) == 2
        rf = [r for r in ranges if r["type"] == "resource_float"][0]
        assert rf["count"] == 4
        assert rf["first"] == 50.0
        assert rf["last"] == 80.2
        sb = [r for r in ranges if r["type"] == "supply_block"][0]
        assert sb["count"] == 1

    def test_sorted_by_severity_then_count(self):
        events = [
            {"time": 10.0, "type": "info_event", "severity": "info"},
            {"time": 20.0, "type": "high_event", "severity": "high"},
            {"time": 20.2, "type": "high_event", "severity": "high"},
            {"time": 30.0, "type": "medium_event", "severity": "medium"},
            {"time": 30.2, "type": "medium_event", "severity": "medium"},
            {"time": 30.4, "type": "medium_event", "severity": "medium"},
        ]
        ranges = _build_event_ranges(events)
        severities = [r["severity"] for r in ranges]
        assert severities[0] == "high"
        assert severities[1] == "medium"
        assert severities[2] == "info"


class TestBuildTimelineData:
    def test_empty(self):
        data = _build_timeline_data([], 100.0)
        assert data == {"ranges": [], "points": [], "duration": 100.0}

    def test_ranged_events_separate_from_points(self):
        ranges = [
            {"type": "supply_block", "severity": "high", "count": 100, "first": 50.0, "last": 200.0, "duration": 150.0},
            {"type": "expansion_started", "severity": "info", "count": 1, "first": 120.0, "last": 120.0, "duration": 0},
        ]
        data = _build_timeline_data(ranges, 250.0)
        assert len(data["ranges"]) == 1
        assert data["ranges"][0]["type"] == "supply_block"
        assert len(data["points"]) == 1
        assert data["points"][0]["type"] == "expansion_started"
        assert data["duration"] == 250.0

    def test_timeline_struct_includes_all_fields(self):
        ranges = [
            {"type": "supply_block", "severity": "high", "count": 50, "first": 100.0, "last": 300.0, "duration": 200.0},
        ]
        data = _build_timeline_data(ranges, 400.0)
        r = data["ranges"][0]
        assert r["type"] == "supply_block"
        assert r["severity"] == "high"
        assert r["start"] == 100.0
        assert r["end"] == 300.0
        assert r["count"] == 50


class TestComputeMetricsEfficiency:
    def test_efficiency_calculation(self):
        features = [
            {"minerals": 50, "vespene": 10, "worker_count": 6, "supply_used": 6, "supply_cap": 15,
             "army_count": 0, "our_army_value": 0, "enemy_army_value": 0,
             "our_t3_count": 0, "enemy_t3_count": 0,
             "collected_minerals": 5000, "collected_vespene": 2000, "bases": []},
        ] * 100
        events = []
        metrics = _compute_metrics(features, events)
        assert metrics["collected_minerals"] == 5000
        assert metrics["collected_vespene"] == 2000
        assert metrics["mineral_efficiency"] > 0
        assert metrics["vespene_efficiency"] > 0

    def test_efficiency_zero_collected(self):
        features = [
            {"minerals": 50, "vespene": 10, "worker_count": 6, "supply_used": 6, "supply_cap": 15,
             "army_count": 0, "our_army_value": 0, "enemy_army_value": 0,
             "our_t3_count": 0, "enemy_t3_count": 0,
             "collected_minerals": 0, "collected_vespene": 0, "bases": []},
        ]
        events = []
        metrics = _compute_metrics(features, events)
        assert metrics["collected_minerals"] == 0
        assert metrics["collected_vespene"] == 0

    def test_army_metrics_peak_values(self):
        features = [
            {"minerals": 0, "vespene": 0, "worker_count": 6, "supply_used": 10, "supply_cap": 100,
             "army_count": 5, "our_army_value": 500, "enemy_army_value": 800,
             "our_t3_count": 0, "enemy_t3_count": 1,
             "collected_minerals": 1000, "collected_vespene": 500, "bases": []},
            {"minerals": 0, "vespene": 0, "worker_count": 6, "supply_used": 80, "supply_cap": 200,
             "army_count": 40, "our_army_value": 8000, "enemy_army_value": 12000,
             "our_t3_count": 3, "enemy_t3_count": 5,
             "collected_minerals": 15000, "collected_vespene": 6000, "bases": []},
        ]
        events = []
        metrics = _compute_metrics(features, events)
        assert metrics["max_supply"] == 80
        assert metrics["max_supply_cap"] == 200
        assert metrics["max_army_size"] == 40
        assert metrics["our_army_value_peak"] == 8000
        assert metrics["enemy_army_value_peak"] == 12000
        assert metrics["our_t3_peak"] == 3
        assert metrics["enemy_t3_peak"] == 5
