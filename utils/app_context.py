"""Contexto mínimo da aplicação local sem autenticação."""

from database.connection import get_session
from services import BootstrapService


def get_operational_user_id() -> int:
    with get_session() as session:
        return BootstrapService(session).get_or_create_operational_user()
