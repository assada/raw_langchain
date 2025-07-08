import base64
import json
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import logging


logger = logging.getLogger(__name__)

# TODO: Absolute bullshit! 
class AuthMiddleware(BaseHTTPMiddleware):    
    def __init__(self, app, for_paths: Optional[list] = None):
        super().__init__(app)
        # self.auth_service = AuthService()
        self.for_paths = for_paths or ["/api/v1/chat"]

    def get_auth_token(self, auth_header: str):
        if not auth_header:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        auth_token = auth_header.split(" ")[1]
        if not auth_token:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        return auth_token
    
    async def dispatch(self, request: Request, call_next):
        if not any(request.url.path.startswith(path) for path in self.for_paths):
            return await call_next(request)
        
        logger.debug(f"Checking auth for path: {request.url.path}")
        try:
            auth_token = self.get_auth_token(request.headers.get("Authorization"))

            logger.debug(f"Auth token: {auth_token}")
            
            decoded_auth_token = json.loads(base64.b64decode(auth_token).decode("utf-8"))
            logger.debug(f"Decoded auth token: {decoded_auth_token}")

            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication failed"}
            )
