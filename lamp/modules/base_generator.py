from abc import ABC
from typing import Dict


class BaseGenerator(ABC):  # noqa: B024
    def __init__(self, config: Dict):
        self._config = config
        self._logger = self._config.get('logger')
