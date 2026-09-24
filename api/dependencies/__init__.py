"""Dependencies compartilhadas da API."""

from api.dependencies.auth import get_current_user
from api.dependencies.database import get_session
from api.dependencies.settings import get_api_settings

__all__ = ["get_api_settings", "get_current_user", "get_session"]
