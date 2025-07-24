from functools import lru_cache
import logging
from langgraph.checkpoint.memory import InMemorySaver

from app.agent.checkpoint.base import BaseCheckpointer

logger = logging.getLogger(__name__)

@lru_cache()
class MemoryCheckpointer(BaseCheckpointer):
    """Memory implementation of the checkpointer."""

    def __init__(self):
        self._checkpointer = None

    async def initialize(self) -> None:
        """Initialize the memory checkpointer."""
        if self._checkpointer is None:
            self._checkpointer = InMemorySaver()
            logger.debug("Memory checkpoint provider initialized")

    async def cleanup(self) -> None:
        """Clean up memory resources."""
        pass
    
    def get_checkpointer(self) -> InMemorySaver:
        """Get the memory checkpointer instance."""
        return self._checkpointer 