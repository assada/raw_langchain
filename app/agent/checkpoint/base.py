import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseCheckpointer(ABC):
    """Base class for checkpointer implementations."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the checkpointer."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass

    @abstractmethod
    def get_checkpointer(self) -> Any:
        """Get the actual checkpointer instance."""
        pass
