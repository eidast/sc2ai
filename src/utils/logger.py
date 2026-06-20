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
    logger.info("step=%d features=%s", iteration, features)
