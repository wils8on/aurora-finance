"""Aplicação FastAPI do Aurora Finance."""

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.config import ApiSettings, Environment, load_settings
from api.errors import register_error_handlers
from api.routes import accounts_router, categories_router, health_router


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    configured = settings or load_settings()
    configured.validate()

    docs_url = "/docs" if configured.environment != Environment.PRODUCTION else None
    openapi_url = (
        "/openapi.json" if configured.environment != Environment.PRODUCTION else None
    )
    application = FastAPI(
        title="Aurora Finance API",
        docs_url=docs_url,
        openapi_url=openapi_url,
    )
    application.state.settings = configured

    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(configured.cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    @application.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID") or str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    register_error_handlers(application)
    application.include_router(health_router, prefix=configured.api_prefix)
    application.include_router(accounts_router, prefix=configured.api_prefix)
    application.include_router(categories_router, prefix=configured.api_prefix)
    return application


app = create_app()
