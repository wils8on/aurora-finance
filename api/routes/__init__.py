"""Routers da API v1."""

from api.routes.accounts import router as accounts_router
from api.routes.categories import router as categories_router
from api.routes.health import router as health_router

__all__ = ["accounts_router", "categories_router", "health_router"]
