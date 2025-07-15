import logging
from typing import Dict, Type

from app.agent.checkpoint.base import CheckpointProvider
from app.agent.checkpoint.providers import (
    MemoryCheckpointProvider,
    PostgresCheckpointProvider,
)
from app.bootstrap.config import AppConfig
from app.infrastructure.database.connection import DatabaseConnectionFactory

logger = logging.getLogger(__name__)


class CheckpointFactory:
    _providers: Dict[str, Type[CheckpointProvider]] = {
        "memory": MemoryCheckpointProvider,
        "postgres": PostgresCheckpointProvider,
    }

    @classmethod
    def create_provider(cls, config: AppConfig) -> CheckpointProvider:
        checkpoint_type = config.checkpoint_type.lower()

        if checkpoint_type not in cls._providers:
            raise ValueError(
                f"Unsupported checkpoint type: {checkpoint_type}. "
            )

        if checkpoint_type == "memory":
            provider = MemoryCheckpointProvider()
        elif checkpoint_type == "postgres":
            database_connection = DatabaseConnectionFactory.create_connection(config)
            provider = PostgresCheckpointProvider(database_connection)
        else:
            raise ValueError(f"Unsupported checkpoint type: {checkpoint_type}")

        logger.debug(f"Created checkpoint provider: {checkpoint_type}")
        return provider

    @classmethod
    def get_supported_types(cls) -> list[str]:
        return list(cls._providers.keys())
