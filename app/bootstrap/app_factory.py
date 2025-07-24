from uuid import uuid4

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
# from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator

from app.http.middleware.auth_middleware import AuthMiddleware
from app.http.middleware.cors_middleware import setup_cors_middleware, CORSConfig
from app.utils.utils import is_valid_uuid4
from .config import AppConfig
from ..http.routes import thread_router, runs_router, health_router


def create_app(config: AppConfig) -> FastAPI:
    app = FastAPI(
        title="Raw LangGraph",
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

    app.include_router(runs_router, prefix="/api/v1")
    app.include_router(thread_router, prefix="/api/v1")
    app.include_router(health_router, prefix="/api/v1")

    # FastAPIInstrumentor.instrument_app(app, excluded_urls="/api/v1/health*,/docs,/metrics,/openapi.json")
    Instrumentator(
        excluded_handlers=["/docs", "/metrics", "/api/v1/health*", "/openapi.json"],
    ).instrument(app).expose(app)

    try:
        app.mount("/", StaticFiles(directory=config.static_files_directory, html=True), name="frontend")
    except RuntimeError:
        pass

    return app
