from datetime import datetime, UTC
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi import Request

from app.bootstrap.config import get_config
from app.http.controllers import ThreadController
from app.http.requests import FeedbackRequest
from app.http.responses import ErrorResponse
from app.models import Thread
from app.repositories import ThreadRepository

thread_router = APIRouter(tags=["threads"])
thread_controller = ThreadController(get_config())


@thread_router.get(
    "/threads/{thread_id}",
    responses={"404": {"model": ErrorResponse}, "422": {"model": ErrorResponse}},
)
async def get_thread(
        thread: Thread = Depends(ThreadRepository.get_thread_by_id),
        request: Request = None,
):
    return {
        "thread_id": thread.id,
        "created_at": datetime.now(tz=UTC).isoformat(),
        "updated_at": datetime.now(tz=UTC).isoformat(),
        "metadata": {
            "title": "Thread Title",
            "user_id": request.state.user.id if request and request.state.user else None,
        },
        "status": "idle"
    }


@thread_router.delete(
    "/threads/{thread_id}",
    response_model=None,
    status_code=204,
    responses={"404": {"model": ErrorResponse}, "422": {"model": ErrorResponse}},
)
async def delete_thread(
        thread: Thread = Depends(ThreadRepository.get_thread_by_id),
        request: Request = None,
) -> Optional[ErrorResponse]:
    # await ThreadRepository.delete_thread(thread.id)
    return


@thread_router.get(
    "/threads/{thread_id}/history",
    responses={"404": {"model": ErrorResponse}, "422": {"model": ErrorResponse}}
)
async def get_thread_history(
        thread: Thread = Depends(ThreadRepository.get_thread_by_id),
        request: Request = None,
):
    return await thread_controller.get_thread_history(request.state.user, thread)


@thread_router.post("/threads/{thread_id}/feedback")
async def post_thread_feedback(
        request_body: FeedbackRequest,
        thread: Thread = Depends(ThreadRepository.get_thread_by_id),
        request: Request = None
):
    return await thread_controller.feedback(request_body, request.state.user, thread)
