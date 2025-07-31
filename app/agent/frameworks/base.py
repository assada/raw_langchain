from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from app.agent.config import EnvironmentConfig
from app.bootstrap.config import AppConfig
from app.models import Thread, User

logger = logging.getLogger(__name__)


class AgentInstance(ABC):
    def __init__(self, agent_id: str, config: EnvironmentConfig):
        self.agent_id = agent_id
        self.config = config

    @abstractmethod
    async def stream_response(
            self, message: str, thread: Thread, user: User
    ) -> AsyncGenerator[dict[str, Any]]:
        pass

    @abstractmethod
    async def load_history(
            self, thread: Thread, user: User
    ) -> AsyncGenerator[dict[str, Any]]:
        pass


class AgentFramework(ABC):
    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Name of the framework (e.g., 'langgraph', 'llamaindex', 'google_adk')."""
        pass

    @abstractmethod
    async def create_agent(
            self,
            agent_id: str,
            agent_config: EnvironmentConfig,
            global_config: AppConfig
    ) -> AgentInstance:
        """Create an agent instance for this framework."""
        pass
