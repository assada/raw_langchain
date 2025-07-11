from app.models import User
from fastapi import HTTPException, Path
import logging


logger = logging.getLogger(__name__)


class UserRepository:
    async def get_user_by_id(user_id: int = Path(..., description="User ID")) -> User:
        try:
            if user_id <= 0:
                raise HTTPException(status_code=400, detail="Invalid user ID")
            
            # TODO: get user from database or api?
            user = User(id=user_id, email=f"user{user_id}@example.com")
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            logger.info(f"Resolved user: {user.id} - {user.email}")
            return user
            
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resolving user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")