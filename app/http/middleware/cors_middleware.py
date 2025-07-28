from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


class CORSConfig:
    def __init__(
            self,
            allow_origins: list[str] | None = None,
            allow_credentials: bool | None = True,
            allow_methods: list[str] | None = None,
            allow_headers: list[str] | None = None
    ):
        self.allow_origins = allow_origins or ["*"]
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]


def setup_cors_middleware(app: FastAPI, config: CORSConfig | None = None) -> None:
    if config is None:
        config = CORSConfig()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allow_origins,
        allow_credentials=bool(config.allow_credentials),
        allow_methods=config.allow_methods,
        allow_headers=config.allow_headers,
    )
