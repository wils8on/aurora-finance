"""Login, logout e identidade da sessão atual."""
from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from api.config import ApiSettings
from api.dependencies import get_api_settings, get_current_user, get_session
from api.dependencies.auth import validate_login_origin
from api.schemas.auth import AuthenticatedUser, AuthSessionResponse, LoginRequest, LogoutResponse
from models import User
from services import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

def _response(user: User, csrf_token: str) -> AuthSessionResponse:
    return AuthSessionResponse(user=AuthenticatedUser(id=user.id, name=user.name, email=user.email, currency=user.currency), csrf_token=csrf_token)

@router.post("/login", response_model=AuthSessionResponse, dependencies=[Depends(validate_login_origin)])
def login(payload: LoginRequest, response: Response, session: Annotated[Session, Depends(get_session)], settings: Annotated[ApiSettings, Depends(get_api_settings)]) -> AuthSessionResponse:
    service = AuthService(session)
    user = service.authenticate(payload.email, payload.password)
    created = service.create_session(user, lifetime_hours=settings.session_lifetime_hours)
    response.set_cookie(key=settings.session_cookie_name, value=created.token, max_age=settings.session_lifetime_hours * 3600, httponly=True, secure=settings.cookie_secure, samesite=settings.cookie_samesite, path=settings.api_prefix)
    return _response(user, created.record.csrf_token)

@router.get("/me", response_model=AuthSessionResponse)
def me(request: Request, current_user: Annotated[User, Depends(get_current_user)]) -> AuthSessionResponse:
    return _response(current_user, request.state.auth_session.csrf_token)

@router.post("/logout", response_model=LogoutResponse)
def logout(request: Request, response: Response, _current_user: Annotated[User, Depends(get_current_user)], session: Annotated[Session, Depends(get_session)], settings: Annotated[ApiSettings, Depends(get_api_settings)]) -> LogoutResponse:
    AuthService(session).revoke(request.state.auth_session)
    response.delete_cookie(settings.session_cookie_name, path=settings.api_prefix, secure=settings.cookie_secure, httponly=True, samesite=settings.cookie_samesite)
    return LogoutResponse()
