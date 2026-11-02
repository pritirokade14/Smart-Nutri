from importlib.metadata import PackageNotFoundError, version

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings, get_settings
from app.core.errors import CatchAllMiddleware, install_error_handlers
from app.core.logging import configure_logging
from app.features.health.router import router as health_router

ROUTERS: list[APIRouter] = [health_router]


def _version() -> str:
    try:
        return version("smartnutri-backend")
    except PackageNotFoundError:
        return "0.0.0"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.environment)
    app = FastAPI(title="SmartNutri API", version=_version())
    app.add_middleware(CatchAllMiddleware)  # innermost
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    install_error_handlers(app)
    for router in ROUTERS:
        app.include_router(router)
    return app
