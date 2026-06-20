import logging

from src.utils.logger import log_features


def test_log_features_emits_feature_dictionary(caplog):
    features = {
        "minerals": 50,
        "vespene": 0,
        "supply_used": 12,
        "supply_cap": 15,
        "worker_count": 12,
        "army_count": 0,
        "enemy_visible_units": 0,
        "game_time_seconds": 9.5,
        "expansion_count": 1,
    }
    logger = logging.getLogger("test_log_features_emits_feature_dictionary")

    with caplog.at_level(logging.INFO, logger=logger.name):
        log_features(logger, features, 44)

    assert "features={" in caplog.text
    assert "'minerals': 50" in caplog.text
    assert "'game_time_seconds': 9.5" in caplog.text
