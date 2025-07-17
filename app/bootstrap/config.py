import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class AppConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    reload: bool = False

    static_files_directory: str = "frontend/dist"

    secret_key: Optional[str] = None

    cors_origins: list = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]

    database_url: Optional[str] = None
    checkpoint_type: str = "memory"  # Options: memory, postgres

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_config() -> AppConfig:
    return AppConfig(
        debug=os.getenv("DEBUG", "false").lower() == "true",
        reload=os.getenv("RELOAD", "false").lower() == "true",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        static_files_directory=os.getenv("STATIC_FILES_DIR", "frontend/dist"),
        secret_key=os.getenv("SECRET_KEY"),
        cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        database_url=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/raw_langgraph"),
        checkpoint_type=os.getenv("CHECKPOINT_TYPE", "memory"),
    )
