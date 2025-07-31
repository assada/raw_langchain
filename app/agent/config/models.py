from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)

class EnvironmentConfig(BaseModel):
    framework: str # Options: "langgraph", "llamaindex", "google_adk"
    graph_class: str | None = None
    prompt_source: str = "file"  # Options: "langfuse", "file"
    custom_settings: dict[str, Any] | None = None


class AgentConfig(BaseModel):
    name: str
    description: str | None = None
    production: EnvironmentConfig
    development: EnvironmentConfig | None = None

    def get_config_for_environment(self, environment: str) -> EnvironmentConfig:
        logger.warning(f"get_config_for_environment: {environment}")
        if environment == "production":
            return self.production
        elif environment == "development" and self.development:
            return self.development
        else:
            # Fallback to production if environment not found
            return self.production