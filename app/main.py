from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import register_error_handlers
from app.api.routes import cities, health
from app.core.config import Environment, Settings, get_settings
from app.core.database import Database
from app.core.logging import configure_logging
from app.core.middleware import (
    BodySizeLimitMiddleware,
    RateLimitMiddleware,
    RequestContextMiddleware,
)
from app.integrations.geocoding.yandex import YandexGeocodingClient


def create_app(
    settings: Settings | None = None,
    *,
    geocoder_client: object | None = None,
    redis_client: object | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database = Database(settings.database_url)
        await database.connect()
        if settings.auto_create_schema:
            await database.create_schema()

        app.state.db = database
        app.state.redis = redis_client
        app.state.redis_owned = False
        app.state.geocoder = geocoder_client or YandexGeocodingClient(
            api_key=settings.yandex_geocoder_api_key,
            base_url=settings.yandex_geocoder_url,
            timeout_seconds=settings.http_timeout_seconds,
        )
        app.state.geocoder_owned = geocoder_client is None

        if settings.rate_limit_enabled and redis_client is None:
            from redis.asyncio import Redis

            app.state.redis = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=settings.redis_timeout_seconds,
                socket_timeout=settings.redis_timeout_seconds,
            )
            app.state.redis_owned = True

        try:
            yield
        finally:
            if app.state.geocoder_owned and hasattr(app.state.geocoder, "close"):
                await app.state.geocoder.close()
            if app.state.redis_owned and app.state.redis is not None:
                await app.state.redis.aclose()
            await database.close()

    docs_enabled = settings.docs_enabled and (
        settings.environment != Environment.PRODUCTION or settings.docs_enabled_in_production
    )
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if settings.openapi_enabled else None,
        lifespan=lifespan,
    )
    app.state.settings = settings

    register_error_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(BodySizeLimitMiddleware)
    app.add_middleware(RequestContextMiddleware)

    app.include_router(health.router)
    app.include_router(cities.router)
    return app


app = create_app()
