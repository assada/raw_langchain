from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class AppConfig(BaseModel):    
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    reload: bool = False
    
    agent_model: str = "gpt-4o-mini"
    agent_prompt: str = "You are a helpful assistant"
    
    static_files_directory: str = "frontend/dist"
    
    secret_key: Optional[str] = None
    
    cors_origins: list = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_config() -> AppConfig:
    return AppConfig(
        debug=os.getenv("DEBUG", "false").lower() == "true",
        reload=os.getenv("RELOAD", "false").lower() == "true",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        agent_model=os.getenv("AGENT_MODEL", "gpt-4o-mini"),
        agent_prompt=os.getenv("AGENT_PROMPT", "You are a helpful assistant"),
        static_files_directory=os.getenv("STATIC_FILES_DIR", "frontend/dist"),
        secret_key=os.getenv("SECRET_KEY"),
        cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    )