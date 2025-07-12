import logging
from datetime import datetime

from fastapi import APIRouter

logger = logging.getLogger(__name__)

health_router = APIRouter(prefix="/health", tags=["health"])


@health_router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "enterprise-chat-api"
    }


@health_router.get("/detailed")
async def detailed_health_check():
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "enterprise-chat-api",
            "components": {
                "chat_service": "healthy",
                "agent": "healthy",
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "enterprise-chat-api",
            "error": str(e)
        }
