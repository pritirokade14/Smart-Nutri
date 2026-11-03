from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version

import httpx
from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.body_limit import BodySizeLimitMiddleware
from app.core.config import Settings, get_settings
from app.core.consent import CONSENT_RESPONSES, gate_for
from app.core.errors import ERROR_RESPONSES, CatchAllMiddleware, install_error_handlers
from app.core.logging import configure_logging
from app.core.observability import init_observability, shutdown_observability
from app.core.security import JwksCache
from app.core.security_headers import SecurityHeadersMiddleware
from app.db.session import build_engine, build_sessionmaker
from app.features.analyze.router import router as analyze_router
from app.features.auth_hooks.router import router as auth_hooks_router
from app.features.consents.router import router as consents_router
from app.features.health.router import router as health_router
from app.features.me.router import router as me_router
from app.features.meals.router import router as meals_router
from app.features.members.router import router as members_router
from app.features.methodology.router import router as methodology_router
from app.features.products.router import router as products_router
from app.features.reports.router import router as reports_router
from app.features.scans.router import router as scans_router
from app.features.voice.router import router as voice_router
from app.integrations.openfoodfacts import SearchThrottle

ROUTERS: list[APIRouter] = [
    health_router,
    me_router,
    products_router,
    analyze_router,
    scans_router,
    consents_router,
    members_router,
    meals_router,
    voice_router,
    methodology_router,
    reports_router,
    auth_hooks_router,
]

# Router prefix -> feature in app.core.consent.REQUIRED. Every route of these routers gets the
# consent gate (Plan 8 Task 1). Plans 6 and 7 mount /v1/meals and /v1/voice: listing them here
# now means they are gated as soon as their routers join ROUTERS.
CONSENT_GATES: dict[str, str] = {
    "/v1/analyze": "analyze",
    "/v1/scans": "scans",
    "/v1/voice": "voice",
    "/v1/meals": "meals",
}


def _include(app: FastAPI, router: APIRouter) -> None:
    feature = CONSENT_GATES.get(router.prefix)
    if feature is None:
        app.include_router(router)
        return
    # Router-level dependencies run before the route's own (e.g. limit()), so a refused call
    # costs no quota.
    app.include_router(
        router, dependencies=[Depends(gate_for(feature))], responses=CONSENT_RESPONSES
    )


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
    prod = settings.environment == "prod"

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
        # No interactive docs or live schema in prod: the contract is exported by script.
        **({"docs_url": None, "redoc_url": None, "openapi_url": None} if prod else {}),
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.off_http = httpx.AsyncClient()  # shared by get_off_client; closed in lifespan
    # One OFF search budget for the whole process (I4), shared by every request.
    app.state.off_search_throttle = SearchThrottle(settings.off_search_per_minute)
    app.state.sessionmaker = build_sessionmaker(engine)
    app.state.jwks_cache = JwksCache(settings.supabase_jwks_url)
    app.add_middleware(CatchAllMiddleware)  # innermost
    # Before routing, but inside CORS so a browser can read the 413 (I2).
    app.add_middleware(BodySizeLimitMiddleware)
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
    app.add_middleware(SecurityHeadersMiddleware, hsts=prod)  # outermost: every response
    install_error_handlers(app)
    for router in ROUTERS:
        _include(app, router)
    return app
