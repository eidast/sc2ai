import logging


def setup_logger(name: str = "sc2ai", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S"
            )
        )
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def log_features(logger: logging.Logger, features: dict, iteration: int):
    logger.info(
        "step=%d minerals=%d gas=%d supply=%d/%d workers=%d army=%d enemy=%d "
        "expansions=%d time=%.1fs",
        iteration,
        features["minerals"],
        features["vespene"],
        features["supply_used"],
        features["supply_cap"],
        features["worker_count"],
        features["army_count"],
        features["enemy_visible_units"],
        features["expansion_count"],
        features["game_time_seconds"],
    )
