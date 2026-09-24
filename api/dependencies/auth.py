"""Usuário operacional explícito para desenvolvimento; não é autenticação."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.config import ApiSettings, Environment
from api.dependencies.database import get_session
from api.dependencies.settings import get_api_settings
from models import User


def get_current_user(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[ApiSettings, Depends(get_api_settings)],
) -> User:
    """Resolve o usuário DEV configurado sem aceitar user_id do cliente."""
    if settings.environment == Environment.PRODUCTION:
        raise RuntimeError("O current_user DEV é proibido em produção.")
    if not settings.dev_user_email:
        raise RuntimeError(
            "AURORA_DEV_USER_EMAIL deve identificar um usuário ativo existente."
        )
    user = session.scalar(
        select(User).where(
            User.email == settings.dev_user_email,
            User.is_active.is_(True),
        )
    )
    if user is None:
        raise RuntimeError(
            "AURORA_DEV_USER_EMAIL não corresponde a um usuário ativo existente."
        )
    return user
