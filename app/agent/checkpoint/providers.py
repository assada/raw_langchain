import logging

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.agent.checkpoint.base import CheckpointProvider
from app.infrastructure.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class MemoryCheckpointProvider(CheckpointProvider):
    def __init__(self):
        self._checkpointer: InMemorySaver = InMemorySaver()

    async def get_checkpointer(self):
        return self._checkpointer

    async def initialize(self) -> None:
        logger.debug("Memory checkpoint provider initialized")


class PostgresCheckpointProvider(CheckpointProvider):
    def __init__(self, database_connection: DatabaseConnection):
        self.database_connection = database_connection
        self._checkpointer: AsyncPostgresSaver = None

    async def get_checkpointer(self):
        if self._checkpointer is None:
            connection = await self.database_connection.get_async_connection()
            self._checkpointer = AsyncPostgresSaver(conn=connection)
            logger.debug("PostgreSQL checkpoint saver created")
        return self._checkpointer

    async def initialize(self) -> None:
        try:
            checkpointer: AsyncPostgresSaver = await self.get_checkpointer()
            await checkpointer.setup()
            logger.debug("PostgreSQL checkpoint provider initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL checkpoint provider: {e}")
            raise
