import logging
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException, Depends
from langfuse import Langfuse
from sse_starlette.sse import EventSourceResponse

from app.agent.checkpoint.factory import get_checkpoint_provider
from app.agent.graph.demo.demo_graph import DemoGraph
from app.agent.services import AgentService
from app.bootstrap.config import AppConfig
from app.http.requests import FeedbackRequest
from app.models import User, Thread
from app.repositories import UserRepository, ThreadRepository

logger = logging.getLogger(__name__)


class ThreadController:
    def __init__(self, config: AppConfig):
        self.config = config
        self.checkpointer_provider = get_checkpoint_provider()
        self._graph = None
        self._agent_service = None
        self._langfuse = None

    async def _initialize(self):  # TODO: refactor this. We should support multiple graphs
        if self._graph is None:
            self._langfuse = Langfuse(
                debug=False,
            )
            await self.checkpointer_provider.initialize()
            checkpointer = await self.checkpointer_provider.get_checkpointer()
            self._graph = DemoGraph(checkpointer, self._langfuse).build_graph()
            self._agent_service = AgentService(self._graph, self._langfuse)

    async def stream(
            self,
            query: str,
            thread_id: UUID,
            metadata: Optional[Dict[str, Any]],
    ):

        if not "user_id" in metadata:
            raise HTTPException(status_code=400, detail="User is required")

        thread = await ThreadRepository.get_thread_by_id(str(thread_id))
        user = await UserRepository.get_user_by_id(str(metadata["user_id"]))

        try:
            await self._initialize()
            logger.debug(f"Received chat request: {query[:50]}...")

            return EventSourceResponse(
                self._agent_service.stream_response(query, thread, user),
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                }
            )
        except Exception as e:
            logger.error(f"Error processing thread request: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def get_thread_history(
            self,
            user: User = Depends(UserRepository.get_user_by_id),
            thread: Thread = Depends(ThreadRepository.get_thread_by_id)
    ):
        try:
            await self._initialize()
            return EventSourceResponse(
                self._agent_service.load_history(thread, user),
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                }
            )
        except Exception as e:
            logger.error(f"Error fetching thread history: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def feedback(
            self,
            request: FeedbackRequest,
            user: User = Depends(UserRepository.get_user_by_id),
            thread: Thread = Depends(ThreadRepository.get_thread_by_id)
    ):
        return await self._agent_service.add_feedback(
            trace=request.trace_id,
            feedback=request.feedback,
            thread=thread,
            user=user
        )
