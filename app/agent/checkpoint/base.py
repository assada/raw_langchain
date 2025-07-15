import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class CheckpointProvider(ABC):
    @abstractmethod
    async def get_checkpointer(self):
        pass

    @abstractmethod
    async def initialize(self) -> None:
        pass
