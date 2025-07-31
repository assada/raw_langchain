from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from app.agent.config import EnvironmentConfig
from app.agent.frameworks.base import AgentFramework, AgentInstance
from app.agent.prompt import create_prompt_provider
from app.bootstrap.config import AppConfig
from app.models import Thread, User

logger = logging.getLogger(__name__)


class LlamaIndexAgentInstance(AgentInstance):
    def __init__(
        self, 
        agent_id: str, 
        config: EnvironmentConfig,
        llamaindex_agent: Any = None
    ):
        super().__init__(agent_id, config)
        self.llamaindex_agent = llamaindex_agent
        logger.debug(f"Created LlamaIndex agent instance: {agent_id}")

    async def stream_response( # type: ignore[override]
            self, message: str, thread: Thread, user: User
    ) -> AsyncGenerator[dict[str, Any]]:
        if self.llamaindex_agent:
            async for event in self.llamaindex_agent.stream_response(message, thread, user):
                yield event
        else:
            logger.warning(f"No LlamaIndex agent configured for {self.agent_id}")
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "ai_message",
                    "content": f"LlamaIndex agent '{self.agent_id}' received: {message}",
                    "metadata": {"agent": self.agent_id, "framework": "llamaindex"}
                })
            }
            yield {
                "event": "end",
                "data": json.dumps({"status": "completed"})
            }

    async def load_history( # type: ignore[override]
            self, thread: Thread, user: User
    ) -> AsyncGenerator[dict[str, Any]]:
        if self.llamaindex_agent:
            async for event in self.llamaindex_agent.load_history(thread, user):
                yield event
        else:
            logger.info(f"Loading history for thread {thread.id} with LlamaIndex agent {self.agent_id}")
            yield {
                "event": "end",
                "data": json.dumps({"status": "completed", "message": "No history available"})
            }


class LlamaIndexFramework(AgentFramework):
    @property
    def framework_name(self) -> str:
        return "llamaindex"

    async def create_agent(
            self,
            agent_id: str,
            agent_config: EnvironmentConfig,
            global_config: AppConfig
    ) -> AgentInstance:
        logger.debug(f"Creating LlamaIndex agent: {agent_id}")

        prompt_provider = create_prompt_provider(
            prompt_source=agent_config.prompt_source,
            langfuse_client=None,
            prompt_dir=global_config.prompt_dir
        )
        
        llamaindex_agent = None

        if agent_config.class_name:
            try:
                agent_class = self._load_agent_class(agent_config.class_name)
                llamaindex_agent = agent_class(
                    prompt_provider=prompt_provider,
                    custom_settings=agent_config.custom_settings
                )
                logger.debug(f"Successfully created {agent_config.class_name} instance")
            except Exception as e:
                logger.error(f"Failed to create LlamaIndex agent {agent_config.class_name}: {e}")
        
        return LlamaIndexAgentInstance(
            agent_id=agent_id,
            config=agent_config,
            llamaindex_agent=llamaindex_agent
        )
