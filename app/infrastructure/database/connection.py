from abc import ABC, abstractmethod
from typing import Any

from app.bootstrap.config import AppConfig


class DatabaseConnection(ABC):
    @abstractmethod
    def get_sync_connection(self) -> Any:
        pass

    @abstractmethod
    async def get_async_connection(self) -> Any:
        pass

    @abstractmethod
    async def get_pool(self) -> Any:
        pass

    @abstractmethod
    def get_connection_string(self) -> str:
        pass

    @abstractmethod
    def close(self) -> Any:
        pass


class DatabaseConnectionFactory:
    @staticmethod
    def create_connection(config: AppConfig) -> DatabaseConnection:
        from app.infrastructure.database.postgresql_connection import (
            PostgreSQLConnection,
        )
        return PostgreSQLConnection(config)
