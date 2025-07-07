from fastapi import APIRouter, HTTPException, Depends
from sse_starlette.sse import EventSourceResponse

from app.app.config import get_config
from ..models.chat import ChatRequest
from ..models.user import User
from ..services.agent_service import AgentService
from ..models.user_repository import UserRepository
from ..models.thread_repository import ThreadRepository
from ..models.thread import Thread
import logging


logger = logging.getLogger(__name__)
config = get_config()

chat_router = APIRouter(prefix="/chat", tags=["chat"])
chat_service = AgentService(config)


@chat_router.post("/{user_id}/thread/{thread_id}/stream")
async def stream_chat(
    request: ChatRequest, 
    user: User = Depends(UserRepository.get_user_by_id),
    thread: Thread = Depends(ThreadRepository.get_thread_by_id)
):
    try:
        logger.info(f"Received chat request: {request.message[:50]}...")
        
        return EventSourceResponse(
            chat_service.stream_response(request.message, thread, user),
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
