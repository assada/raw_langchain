import logging

from fastapi import HTTPException, Depends
from sse_starlette.sse import EventSourceResponse

from app.agent.checkpoint import CheckpointFactory
from app.agent.graph.demo.demo_graph import DemoGraph
from app.agent.services import AgentService
from app.bootstrap.config import AppConfig
from app.http.requests import ChatRequest, FeedbackRequest
from app.models import User, Thread
from app.repositories import UserRepository, ThreadRepository

logger = logging.getLogger(__name__)


class ChatController:
    def __init__(self, config: AppConfig):
        self.config = config
        self.checkpointer_provider = CheckpointFactory.create_provider(config)
        self._graph = None
        self._agent_service = None

    async def _initialize(self):
        if self._graph is None:
            await self.checkpointer_provider.initialize()
            checkpointer = await self.checkpointer_provider.get_checkpointer()
            self._graph = DemoGraph(self.config, checkpointer).build_graph()
            self._agent_service = AgentService(self._graph)

    async def stream_chat(
            self,
            request: ChatRequest,
            user: User = Depends(UserRepository.get_user_by_id),
            thread: Thread = Depends(ThreadRepository.get_thread_by_id)
    ):
        try:
            await self._initialize()
            logger.debug(f"Received chat request: {request.message[:50]}...")

            return EventSourceResponse(
                self._agent_service.stream_response(request.message, thread, user),
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                }
            )
        except Exception as e:
            logger.error(f"Error processing chat request: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def get_chat_history(
            self,
            user: User = Depends(UserRepository.get_user_by_id),
            thread: Thread = Depends(ThreadRepository.get_thread_by_id)
    ):
        try:
            await self._initialize()
            return await self._agent_service.load_history(thread, user)
        except Exception as e:
            logger.error(f"Error fetching chat history: {str(e)}")
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
