from fastapi import APIRouter
from sse_starlette import EventSourceResponse

from app.bootstrap.config import get_config
from app.http.controllers import ThreadController
from app.http.requests import Run

runs_router = APIRouter(tags=["runs"])
thread_controller = ThreadController(get_config())


@runs_router.post("/runs/stream")
async def run_stream(
        request: Run,
) -> EventSourceResponse:
    return await thread_controller.stream(request.input, request.thread_id, request.metadata or {})
