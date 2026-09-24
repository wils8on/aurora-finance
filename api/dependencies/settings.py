"""Acesso à configuração associada à aplicação FastAPI."""

from fastapi import Request

from api.config import ApiSettings


def get_api_settings(request: Request) -> ApiSettings:
    return request.app.state.settings
