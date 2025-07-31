import logging

from app.bootstrap.config import AppConfig
from app.infrastructure.database.connection import DatabaseConnectionFactory

from .base import BaseCheckpointer
from .memory import MemoryCheckpointer
from .postgres import PostgresCheckpointer

logger = logging.getLogger(__name__)


class CheckpointerFactory:
    @classmethod
    async def create(cls, config: AppConfig) -> BaseCheckpointer:
        checkpoint_type = config.checkpoint_type.lower()
        instance: BaseCheckpointer

        if checkpoint_type == "memory":
            instance = MemoryCheckpointer()
        elif checkpoint_type == "postgres":
            database_connection = DatabaseConnectionFactory.create_connection(config)
            instance = PostgresCheckpointer(database_connection)
        else:
            raise ValueError(f"Unsupported checkpointer type: {checkpoint_type}")

        await instance.initialize()
        return instance

    @classmethod
    def get_supported_types(cls) -> list[str]:
        return ["memory", "postgres"]
