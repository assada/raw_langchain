import logging

from fastapi import HTTPException, Path

from app.models import Thread

logger = logging.getLogger(__name__)


class ThreadRepository:
    @staticmethod
    async def get_thread_by_id(
        thread_id: str = Path(..., description="Thread ID"),
    ) -> Thread:
        try:
            if thread_id is None or not isinstance(thread_id, str):
                raise HTTPException(status_code=400, detail="Invalid thread ID")

            # TODO: get thread from database
            thread = Thread(
                id=thread_id,
                metadata={
                    "title": "Sample Thread",
                },
                agent_id="demo_agent"
            )

            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")

            logger.debug(f"Resolved thread: {thread.id}")
            return thread

        except ValueError as ve:
            raise HTTPException(
                status_code=400, detail="Invalid thread ID format"
            ) from ve
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resolving thread {thread_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error") from e
