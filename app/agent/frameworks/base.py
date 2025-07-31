from __future__ import annotations

import importlib
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

    def _load_agent_class(self, agent_class_name: str) -> Any:
        if not agent_class_name or '.' not in agent_class_name:
            raise ValueError(f"Invalid agent class name: {agent_class_name}")
            
        module_name, class_name = agent_class_name.rsplit('.', 1)

        try:
            module = importlib.import_module(module_name)
            return getattr(module, class_name)
        except ImportError as e:
            raise ImportError(f"Could not import module {module_name}: {e}") from e
        except AttributeError as e:
            raise AttributeError(f"Class {class_name} not found in module {module_name}: {e}") from e

    @abstractmethod
    async def create_agent(
            self,
            agent_id: str,
            agent_config: EnvironmentConfig,
            global_config: AppConfig
    ) -> AgentInstance:
        pass
