import logging
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException
from langfuse import Langfuse  # type: ignore[attr-defined]
from langgraph.graph.state import CompiledStateGraph
from sse_starlette.sse import EventSourceResponse

from app.agent.checkpoint.factory import CheckpointerFactory
from app.agent.graph.demo.demo_graph import DemoGraph
from app.agent.prompt import LangfusePromptProvider
from app.agent.services import AgentService
from app.bootstrap.config import AppConfig
from app.http.requests import FeedbackRequest
from app.models import Thread, User
from app.repositories import ThreadRepository, UserRepository

logger = logging.getLogger(__name__)


class ThreadController:
    def __init__(self, config: AppConfig):
        self.config = config
        self._checkpointer_provider: CheckpointerFactory | None = None
        self._graph: CompiledStateGraph[Any, Any, Any] | None = None
        self._agent_service: AgentService | None = None
        self._langfuse: Langfuse | None = None

    async def _initialize(self) -> None:
        if self._graph is None:
            self._langfuse = Langfuse(debug=False)

            if self._checkpointer_provider is None:
                self._checkpointer_provider = await CheckpointerFactory.create(
                    self.config
                )  # type: ignore[assignment]

            checkpointer = await self._checkpointer_provider.get_checkpointer()  # type: ignore[union-attr]
            prompt_provider = LangfusePromptProvider(self._langfuse)
            self._graph = DemoGraph(checkpointer, prompt_provider).build_graph()
            self._agent_service = AgentService(self._graph, self._langfuse)

    async def stream(
        self,
            query: dict[str, Any] | list[Any] | str | float | bool | None,
        thread_id: UUID | None,
        metadata: dict[str, Any] | None,
        user: User,
    ) -> EventSourceResponse:
        thread = await ThreadRepository.get_thread_by_id(str(thread_id))

        try:
            await self._initialize()
            logger.debug(f"Received chat request: {str(query)[:50]}...")

            return EventSourceResponse(
                self._agent_service.stream_response(str(query), thread, user),  # type: ignore[union-attr]
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
            await self._initialize()
            return EventSourceResponse(
                self._agent_service.load_history(thread, user),  # type: ignore[union-attr]
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
        await self._initialize()
        return await self._agent_service.add_feedback(  # type: ignore[union-attr]
            trace=request.trace_id, feedback=request.feedback, thread=thread, user=user
        )
