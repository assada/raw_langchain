import logging
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException
from langfuse import Langfuse  # type: ignore[attr-defined]
from sse_starlette.sse import EventSourceResponse  # type: ignore[attr-defined]

from app.agent.factory import AgentFactory
from app.agent.frameworks.base import AgentInstance
from app.agent.services import AgentService
from app.bootstrap.config import AppConfig
from app.http.requests import FeedbackRequest
from app.models import Thread, User
from app.repositories import ThreadRepository, UserRepository

logger = logging.getLogger(__name__)


class ThreadController:
    def __init__(self, config: AppConfig):
        self.config = config
        self.agent_factory = AgentFactory(config)
        self._agent_instances: dict[str, AgentInstance] = {}
        self._agent_service = AgentService(Langfuse(debug=False))

    async def _get_agent_instance(self, agent_id: str | None = None) -> AgentInstance:
        environment = self.config.environment
        cache_key = f"{agent_id}:{environment}"
        if cache_key in self._agent_instances:
            return self._agent_instances[cache_key]

        agent_instance = await self.agent_factory.create_agent(
            agent_id, environment
        )

        self._agent_instances[cache_key] = agent_instance
        logger.debug(f"Created and cached agent instance: {cache_key}")

        return agent_instance

    async def stream(
        self,
        query: dict[str, Any] | list[Any] | str | float | bool | None,
        thread_id: UUID | None,
        metadata: dict[str, Any] | None,
        user: User,
        agent_id: str | None = None,
    ) -> EventSourceResponse:
        thread = await ThreadRepository.get_thread_by_id(str(thread_id))

        if agent_id and thread.agent_id != agent_id:
            thread.agent_id = agent_id
        effective_agent_id = agent_id or thread.agent_id

        try:
            agent_instance = await self._get_agent_instance(effective_agent_id)
            logger.debug(f"Received chat request: {str(query)[:50]}...")

            return EventSourceResponse(
                agent_instance.stream_response(str(query), thread, user),  # type: ignore[union-attr]
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                },
            )
        except Exception as e:
            logger.error(f"Error processing thread request: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    async def get_thread_history(
        self,
        user: User = Depends(UserRepository.get_user_by_id),  # noqa: B008
        thread: Thread = Depends(ThreadRepository.get_thread_by_id),  # noqa: B008
    ) -> EventSourceResponse:
        try:
            agent_instance = await self._get_agent_instance(thread.agent_id)
            return EventSourceResponse(
                agent_instance.load_history(thread, user),  # type: ignore[union-attr]
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                },
            )
        except Exception as e:
            logger.error(f"Error fetching thread history: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    async def feedback(
        self,
        request: FeedbackRequest,
        user: User = Depends(UserRepository.get_user_by_id),  # noqa: B008
        thread: Thread = Depends(ThreadRepository.get_thread_by_id),  # noqa: B008
    ) -> dict[str, str]:
        return await self._agent_service.add_feedback(  # type: ignore[union-attr]
            trace=request.trace_id, feedback=request.feedback, thread=thread, user=user
        )
