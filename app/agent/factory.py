from __future__ import annotations

import logging

from app.agent.config import AgentConfigLoader
from app.agent.frameworks.base import AgentFramework, AgentInstance
from app.agent.frameworks.google_adk import GoogleADKFramework
from app.agent.frameworks.langgraph import LangGraphFramework
from app.agent.frameworks.llamaindex import LlamaIndexFramework
from app.bootstrap.config import AppConfig

logger = logging.getLogger(__name__)


class AgentFactory:
    def __init__(self, global_config: AppConfig):
        self.global_config = global_config
        self.config_loader = AgentConfigLoader(global_config.agent_config_dir)
        logger.info(f"Loading agent configuration from {self.config_loader.config_directory}")
        self._frameworks: dict[str, AgentFramework] = {}
        self._register_built_in_frameworks()

    def _register_built_in_frameworks(self) -> None:
        self.register_framework(LangGraphFramework())
        self.register_framework(LlamaIndexFramework())
        self.register_framework(GoogleADKFramework())

    def register_framework(self, framework: AgentFramework) -> None:
        self._frameworks[framework.framework_name] = framework
        logger.info(f"Registered framework: {framework.framework_name}")

    async def create_agent(
            self,
            agent_id: str,
            environment: str,
    ) -> AgentInstance:
        agent_config = self.config_loader.get_agent_config(agent_id)
        if not agent_config:
            raise ValueError(f"Agent configuration not found: {agent_id}")

        env_config = agent_config.get_config_for_environment(environment)
        framework_name = env_config.framework

        framework = self._frameworks.get(framework_name)
        if not framework:
            raise ValueError(f"Framework not supported: {framework_name}")

        logger.info(f"Creating agent '{agent_id}' with framework '{framework_name}' for environment '{environment}'")
        return await framework.create_agent(agent_id, env_config, self.global_config)
