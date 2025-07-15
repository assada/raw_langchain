import logging
from typing import Optional

import psycopg
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.bootstrap.config import AppConfig
from app.infrastructure.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class PostgreSQLConnection(DatabaseConnection):
    def __init__(self, config: AppConfig):
        self.config = config
        self._async_connection: Optional[AsyncConnection] = None

    def get_connection_string(self) -> str:
        return self.config.database_url

    def get_sync_connection(self):
        raise NotImplementedError("Sync connection not supported in async implementation")

    async def get_async_connection(self) -> AsyncConnection:
        if self._async_connection is None or self._async_connection.closed:
            try:
                self._async_connection = await psycopg.AsyncConnection.connect(
                    self.get_connection_string(),
                    autocommit=True,  # Mandatory for checkpointing
                    connect_timeout=10,
                    row_factory=dict_row  # Mandatory for checkpointing
                )
            except Exception as e:
                logger.error(f"Failed to establish PostgreSQL async connection: {e}")
                raise

        return self._async_connection

    def close(self) -> None:
        if self._async_connection and not self._async_connection.closed:
            self._async_connection.close()
