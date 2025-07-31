from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.agent.config.models import AgentConfig

logger = logging.getLogger(__name__)


class AgentConfigLoader:
    def __init__(self, config_directory: str = "agents/config"):
        self.config_directory = Path(config_directory)
        self._configs: dict[str, AgentConfig] = {}
        self._load_all_configs()

    def _load_all_configs(self) -> None:
        if not self.config_directory.exists():
            logger.warning(f"Agent config directory {self.config_directory} does not exist")
            return

        for config_file in self.config_directory.glob("*.json"):
            try:
                agent_name = config_file.stem
                with open(config_file, encoding='utf-8') as f:
                    config_data = json.load(f)

                self._configs[agent_name] = AgentConfig(**config_data)
                logger.debug(f"Loaded agent config: {agent_name}")

            except Exception as e:
                logger.error(f"Failed to load agent config {config_file}: {e}")

    def get_agent_config(self, agent_name: str) -> AgentConfig | None:
        return self._configs.get(agent_name)

    def list_available_agents(self) -> list[str]:
        return list(self._configs.keys())

    def get_config_for_environment(
            self, agent_name: str, environment: str = "production"
    ) -> dict[str, Any] | None:
        agent_config = self.get_agent_config(agent_name)
        if not agent_config:
            return None

        env_config = agent_config.get_config_for_environment(environment)
        return env_config.model_dump()
