from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version

import httpx
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings, get_settings
from app.core.errors import ERROR_RESPONSES, CatchAllMiddleware, install_error_handlers
from app.core.logging import configure_logging
from app.core.observability import init_observability, shutdown_observability
from app.core.security import JwksCache
from app.db.session import build_engine, build_sessionmaker
from app.features.analyze.router import router as analyze_router
from app.features.health.router import router as health_router
from app.features.me.router import router as me_router
from app.features.products.router import router as products_router

ROUTERS: list[APIRouter] = [health_router, me_router, products_router, analyze_router]


def _version() -> str:
    try:
        return version("smartnutri-backend")
    except PackageNotFoundError:
        return "0.0.0"


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app. Request-time code reads these settings via `get_app_settings`."""
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    init_observability(settings)
    engine = build_engine(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # app.state.off_http is created eagerly below (works without lifespan, e.g. ASGITransport);
        # the lifespan only closes it.
        try:
            yield
        finally:
            await app.state.off_http.aclose()
            shutdown_observability()
            await engine.dispose()

    app = FastAPI(
        title="SmartNutri API",
        version=_version(),
        lifespan=lifespan,
        responses=ERROR_RESPONSES,
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.off_http = httpx.AsyncClient()  # shared by get_off_client; closed in lifespan
    app.state.sessionmaker = build_sessionmaker(engine)
    app.state.jwks_cache = JwksCache(settings.supabase_jwks_url)
    app.add_middleware(CatchAllMiddleware)  # innermost
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        # Bearer tokens, never cookies: browsers must not send credentials cross-origin.
        allow_credentials=False,
        # Lets the web app read the back-off on 429 responses.
        expose_headers=["Retry-After"],
    )
    install_error_handlers(app)
    for router in ROUTERS:
        app.include_router(router)
    return app
