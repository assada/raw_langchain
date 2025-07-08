from fastapi import APIRouter, Depends

from app.http.requests import ChatRequest
from app.models import User, Thread
from app.repositories import UserRepository, ThreadRepository
from app.http.controllers import ChatController

chat_router = APIRouter(prefix="/chat", tags=["chat"])
chat_controller = ChatController()

@chat_router.post("/{user_id}/thread/{thread_id}/stream")
async def stream_chat(
    request: ChatRequest, 
    user: User = Depends(UserRepository.get_user_by_id),
    thread: Thread = Depends(ThreadRepository.get_thread_by_id)
):
    return await chat_controller.stream_chat(request, user, thread)
