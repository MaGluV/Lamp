import logging
import logging.config

import yaml

from .consts import LOGGER_CONFIG


def get_logger(name):
    with open(LOGGER_CONFIG, 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)

    logger = logging.getLogger(name)
    return logger
