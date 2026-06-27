import logging
import secrets

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src import __version__
from src.infrastructure.config.settings import settings
from src.infrastructure.http.limiter import limiter
from src.infrastructure.http.routes import setup_router

log = logging.getLogger(__name__)


def _session_secret() -> str:
    if settings.SESSION_SECRET:
        return settings.SESSION_SECRET
    # Dev fallback: an in-process random secret. Sessions DON'T survive a
    # restart, and rotating workers invalidate each other's cookies — both
    # acceptable for local dev only. Loudly warn so a forgotten env in
    # staging/prod becomes visible at boot.
    log.warning(
        "SESSION_SECRET is empty — using a process-local random secret. "
        "Sessions will not survive restarts. Set SESSION_SECRET in staging/prod."
    )
    return secrets.token_urlsafe(48)


def create_app() -> FastAPI:
    logging.basicConfig(level=settings.LOG_LEVEL)

    app = FastAPI(
        title="CaaS API",
        version=__version__,
        docs_url=None if settings.HIDE_DOCS else "/caas/docs",
        redoc_url=None if settings.HIDE_DOCS else "/caas/redoc",
        openapi_url=None if settings.HIDE_DOCS else "/caas/openapi.json",
    )

    # Cookie-signed sessions (itsdangerous under the hood, no extra dep).
    app.add_middleware(
        SessionMiddleware,
        secret_key=_session_secret(),
        session_cookie=settings.SESSION_COOKIE_NAME,
        max_age=settings.SESSION_TTL_SECONDS,
        same_site="lax",
        https_only=settings.SESSION_COOKIE_SECURE,
    )

    # slowapi — same limiter singleton across the app, route decorators and
    # the test reset hook.
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    setup_router(app)

    return app
