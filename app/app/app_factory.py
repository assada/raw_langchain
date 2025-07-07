from uuid import UUID, uuid4
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from ..middleware.cors_middleware import setup_cors_middleware, CORSConfig
from ..middleware.auth_middleware import AuthMiddleware
from ..routes.chat_routes import chat_router
from ..routes.health_routes import health_router
from .config import AppConfig

def is_valid_uuid4(uuid_: str) -> bool:
    try:
        return UUID(uuid_).version == 4
    except ValueError:
        return False

def create_app(config: AppConfig) -> FastAPI:
    app = FastAPI(
        title="Test Application",
        description="A test application",
        version="1.0.0",
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
    
    try:
        app.mount("/", StaticFiles(directory=config.static_files_directory, html=True), name="frontend")
    except RuntimeError:
        pass
    
    return app 