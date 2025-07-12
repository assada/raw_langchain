from uuid import UUID, uuid4

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator

from app.http.middleware.auth_middleware import AuthMiddleware
from app.http.middleware.cors_middleware import setup_cors_middleware, CORSConfig
from app.http.routes.chat_routes import chat_router
from app.http.routes.health_routes import health_router
from .config import AppConfig


def is_valid_uuid4(uuid_: str) -> bool:
    try:
        return UUID(uuid_).version == 4
    except ValueError:
        return False


def create_app(config: AppConfig) -> FastAPI:
    app = FastAPI(
        title="Raw Langchain",
        description="A test application",
        version="0.0.1",
        debug=config.debug
    )

    cors_config = CORSConfig(
        allow_origins=config.cors_origins,
        allow_credentials=config.cors_allow_credentials,
        allow_methods=config.cors_allow_methods,
        allow_headers=config.cors_allow_headers
    )
    setup_cors_middleware(app, cors_config)

    app.add_middleware(
        CorrelationIdMiddleware,
        header_name='X-Request-ID',
        update_request_header=True,
        generator=lambda: uuid4().hex,
        validator=is_valid_uuid4,
        transformer=lambda a: a,
    )

    app.add_middleware(AuthMiddleware)

    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(health_router, prefix="/api/v1")

    FastAPIInstrumentor.instrument_app(app)
    Instrumentator(
        excluded_handlers=["/docs", "/metrics", "/api/v1/health", "/openapi.json"],
    ).instrument(app).expose(app)

    try:
        app.mount("/", StaticFiles(directory=config.static_files_directory, html=True), name="frontend")
    except RuntimeError:
        pass

    return app
