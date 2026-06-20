from types import SimpleNamespace

from src.ml.report import generate_report_json, generate_report_md, generate_report_html


def test_generate_report_json_shape():
    features = [
        {"game_time_seconds": 0, "iteration": 0, "supply_used": 6, "supply_cap": 15,
         "worker_count": 6, "army_count": 0, "minerals": 50, "vespene": 0,
         "collected_minerals": 500, "collected_vespene": 200,
         "our_army_value": 0, "enemy_army_value": 0, "our_t3_count": 0, "enemy_t3_count": 0,
         "expansion_count": 1, "enemy_visible_units": 0, "enemy_army_composition": {},
         "our_army_composition": {}, "bases": [{"ideal_workers": 16, "current_workers": 6, "saturation_ratio": 0.375}]},
        {"game_time_seconds": 10, "iteration": 100, "supply_used": 10, "supply_cap": 15,
         "worker_count": 10, "army_count": 0, "minerals": 200, "vespene": 0,
         "collected_minerals": 1500, "collected_vespene": 800,
         "our_army_value": 100, "enemy_army_value": 200, "our_t3_count": 1, "enemy_t3_count": 2,
         "expansion_count": 1, "enemy_visible_units": 2, "enemy_army_composition": {"Marine": 2},
         "our_army_composition": {"Zealot": 1}, "bases": [{"ideal_workers": 16, "current_workers": 10, "saturation_ratio": 0.625}]},
    ]
    events = [
        {"time": 0, "type": "game_start", "severity": "info"},
        {"time": 10, "type": "supply_block", "severity": "high"},
    ]
    bot_info = {"map": "AcropolisLE", "opponent_race": "Terran",
                "opponent_difficulty": "Medium", "result": "defeat"}

    report = generate_report_json("test_match_id", features, events, bot_info)

    assert report["match_id"] == "test_match_id"
    assert report["map"] == "AcropolisLE"
    assert report["opponent_race"] == "Terran"
    assert report["result"] == "defeat"
    assert report["duration_seconds"] == 10
    assert report["max_supply_reached"] == 10
    assert "timeline" in report
    assert "army_snapshots" in report
    assert "metrics" in report
    assert "key_events" in report
    assert "event_ranges" in report
    assert "timeline_data" in report
    assert len(report["timeline"]) == 2
    assert len(report["key_events"]) == 2
    assert report["metrics"]["supply_block_count"] == 1
    assert report["metrics"]["peak_workers"] == 10
    assert report["metrics"]["collected_minerals"] == 1500
    assert report["metrics"]["collected_vespene"] == 800
    assert "mineral_efficiency" in report["metrics"]
    assert "vespene_efficiency" in report["metrics"]
    assert report["metrics"]["max_supply"] == 10
    assert report["metrics"]["max_army_size"] == 0
    assert report["metrics"]["our_army_value_peak"] == 100
    assert report["metrics"]["enemy_army_value_peak"] == 200
    assert report["metrics"]["our_t3_peak"] == 1
    assert report["metrics"]["enemy_t3_peak"] == 2
    assert "saturation_summary" in report["metrics"]


def test_generate_report_md():
    report = {
        "match_id": "test",
        "map": "TestMap",
        "opponent_race": "Terran",
        "opponent_difficulty": "Medium",
        "duration_seconds": 100,
        "result": "victory",
        "max_supply_reached": 50,
        "metrics": {
            "avg_unspent_minerals": 100,
            "avg_unspent_vespene": 50,
            "supply_block_count": 1,
            "peak_workers": 40,
            "worker_target": 70,
            "saturation_summary": [],
        },
        "key_events": [
            {"time": 0, "type": "game_start", "severity": "info"},
        ],
        "army_snapshots": [
            {"time": 0, "our_army_count": 0, "our_composition": {}, "enemy_visible": 0, "enemy_composition": {}},
        ],
    }

    md = generate_report_md(report)
    assert "# Match Report: test" in md
    assert "TestMap" in md
    assert "victory" in md
    assert "Metrics" in md
    assert "supply_block_count" not in md.lower()


def test_generate_report_html_contains_required_elements():
    report = {
        "match_id": "test",
        "map": "TestMap",
        "opponent_race": "Terran",
        "opponent_difficulty": "Medium",
        "duration_seconds": 100,
        "result": "victory",
        "max_supply_reached": 50,
        "timeline": [
            {"supply_used": 6, "time": 0},
            {"supply_used": 15, "time": 50},
        ],
        "metrics": {
            "avg_unspent_minerals": 100,
            "avg_unspent_vespene": 50,
            "collected_minerals": 20000,
            "collected_vespene": 8000,
            "mineral_efficiency": 75.0,
            "vespene_efficiency": 60.0,
            "supply_block_count": 1,
            "peak_workers": 40,
            "worker_target": 70,
            "total_steps": 100,
            "max_supply": 50,
            "max_supply_cap": 200,
            "max_army_size": 25,
            "our_army_value_peak": 5000,
            "enemy_army_value_peak": 8000,
            "our_t3_peak": 2,
            "enemy_t3_peak": 3,
            "saturation_summary": [],
        },
        "key_events": [
            {"time": 0, "type": "game_start", "severity": "info"},
        ],
        "army_snapshots": [
            {"time": 0, "our_army_count": 0, "our_composition": {}, "enemy_visible": 0, "enemy_composition": {}},
        ],
        "event_ranges": [
            {"type": "game_start", "severity": "info", "count": 1, "first": 0, "last": 0, "duration": 0},
        ],
        "timeline_data": {"ranges": [], "points": [], "duration": 100},
    }

    html = generate_report_html(report)
    assert "<!DOCTYPE html>" in html
    assert "SC2AI Match Report" in html
    assert "TestMap" in html
    assert "victory" in html
    assert "Enemy Army" in html
    assert "Our Army" in html
    assert "Base Saturation" in html
    assert "Economy" in html
    assert "Army" in html
    assert "Minerals gathered" in html
    assert "Timeline" in html
    assert "Events" in html
