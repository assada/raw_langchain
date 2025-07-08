from fastapi import HTTPException, Depends
from sse_starlette.sse import EventSourceResponse
import logging

from app.bootstrap.config import get_config
from app.http.requests import ChatRequest
from app.models import User, Thread
from app.repositories import UserRepository, ThreadRepository
from app.agent.services import AgentService

logger = logging.getLogger(__name__)

class ChatController:
    def __init__(self):
        self.config = get_config()
        self.agent_service = AgentService(self.config)
    
    async def stream_chat(
        self, 
        request: ChatRequest, 
        user: User = Depends(UserRepository.get_user_by_id),
        thread: Thread = Depends(ThreadRepository.get_thread_by_id)
    ):
        """Stream chat response from agent"""
        try:
            logger.info(f"Received chat request: {request.message[:50]}...")
            
            return EventSourceResponse(
                self.agent_service.stream_response(request.message, thread, user),
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