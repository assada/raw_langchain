from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


class CORSConfig:
    def __init__(
            self,
            allow_origins: List[str] = None,
            allow_credentials: bool = True,
            allow_methods: List[str] = None,
            allow_headers: List[str] = None
    ):
        self.allow_origins = allow_origins or ["*"]
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]


def setup_cors_middleware(app: FastAPI, config: Optional[CORSConfig] = None) -> None:
    if config is None:
        config = CORSConfig()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allow_origins,
        allow_credentials=config.allow_credentials,
        allow_methods=config.allow_methods,
        allow_headers=config.allow_headers,
    )
