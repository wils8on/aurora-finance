"""Resolução central da identidade autenticada, Origin e CSRF."""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from api.config import ApiSettings
from api.dependencies.database import get_session
from api.dependencies.settings import get_api_settings
from models import User
from services import AuthService, AuthorizationError

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def require_allowed_origin(request: Request, settings: ApiSettings) -> None:
    if request.headers.get("Origin") not in settings.cors_origins:
        raise AuthorizationError("Origem não autorizada.", code="ORIGIN_NOT_ALLOWED")


def validate_login_origin(
    request: Request,
    settings: Annotated[ApiSettings, Depends(get_api_settings)],
) -> None:
    require_allowed_origin(request, settings)


def get_current_user(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[ApiSettings, Depends(get_api_settings)],
) -> User:
    service = AuthService(session)
    auth_session = service.resolve_session(request.cookies.get(settings.session_cookie_name))
    if request.method not in SAFE_METHODS:
        require_allowed_origin(request, settings)
        service.require_csrf(auth_session, request.headers.get("X-CSRF-Token"))
    request.state.auth_session = auth_session
    return auth_session.user
