"""Routers da API v1."""

from api.routes.accounts import router as accounts_router
from api.routes.categories import router as categories_router
from api.routes.health import router as health_router
from api.routes.summaries import router as summaries_router
from api.routes.transactions import router as transactions_router

__all__ = [
    "accounts_router",
    "categories_router",
    "health_router",
    "summaries_router",
    "transactions_router",
]
