from app.models import Thread
from fastapi import HTTPException, Path
import logging


logger = logging.getLogger(__name__)

class ThreadRepository:
    async def get_thread_by_id(thread_id: int = Path(..., description="Thread ID")) -> Thread:
        try:
            if thread_id <= 0:
                raise HTTPException(status_code=400, detail="Invalid thread ID")
            
            # TODO: get thread from database
            thread = Thread(id=thread_id, user_id=1)
            
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
            
            logger.info(f"Resolved thread: {thread.id}")
            return thread
            
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid thread ID format")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resolving thread {thread_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")