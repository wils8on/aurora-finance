"""Tratamento uniforme de erros da API."""

from api.errors.handlers import register_error_handlers

__all__ = ["register_error_handlers"]
