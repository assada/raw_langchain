from fastapi import APIRouter, Depends

from app.bootstrap.config import get_config
from app.http.controllers import ChatController
from app.http.requests import ChatRequest
from app.models import User, Thread
from app.repositories import UserRepository, ThreadRepository

chat_router = APIRouter(prefix="/chat", tags=["chat"])
chat_controller = ChatController(get_config())


@chat_router.post("/{user_id}/thread/{thread_id}/stream")
async def stream_chat(
        request: ChatRequest,
        user: User = Depends(UserRepository.get_user_by_id),
        thread: Thread = Depends(ThreadRepository.get_thread_by_id)
):
    return await chat_controller.stream_chat(request, user, thread)


@chat_router.get("/{user_id}/thread/{thread_id}")
async def get_chat_history(
        user: User = Depends(UserRepository.get_user_by_id),
        thread: Thread = Depends(ThreadRepository.get_thread_by_id)
):
    return await chat_controller.get_chat_history(user, thread)
