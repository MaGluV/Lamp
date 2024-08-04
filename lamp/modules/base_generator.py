from abc import ABC
from typing import Dict

from lamp.utils.logger import get_logger


class BaseGenerator(ABC):  # noqa: B024
    def __init__(self, config: Dict):
        self._logger = get_logger(type(self).__name__)
        self._config = config
