"""Configuração mínima da API por ambiente."""

from dataclasses import dataclass
from enum import Enum
import os

from dotenv import load_dotenv

load_dotenv()

API_PREFIX = "/api/v1"


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


@dataclass(frozen=True)
class ApiSettings:
    environment: Environment
    cors_origins: tuple[str, ...]
    api_prefix: str = API_PREFIX
    session_cookie_name: str = "aurora_session"
    session_lifetime_hours: int = 12
    cookie_secure: bool = False

    def validate(self) -> None:
        if "*" in self.cors_origins:
            raise RuntimeError("CORS wildcard não é permitido.")
        if self.environment == Environment.PRODUCTION:
            if not self.cookie_secure:
                raise RuntimeError("Cookies de produção devem utilizar Secure.")
            if not self.cors_origins or any(not origin.startswith("https://") for origin in self.cors_origins):
                raise RuntimeError("Produção exige origens CORS HTTPS explícitas.")
        if self.session_lifetime_hours < 1 or self.session_lifetime_hours > 720:
            raise RuntimeError("AUTH_SESSION_HOURS deve estar entre 1 e 720.")


def load_settings() -> ApiSettings:
    raw_environment = os.getenv("AURORA_ENV", Environment.DEVELOPMENT.value).strip().lower()
    try:
        environment = Environment(raw_environment)
    except ValueError as error:
        raise RuntimeError(
            "AURORA_ENV deve ser development, test ou production."
        ) from error

    raw_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
    origins = tuple(
        origin.strip()
        for origin in raw_origins.split(",")
        if origin.strip()
    )
    raw_cookie_secure = os.getenv("AUTH_COOKIE_SECURE")
    cookie_secure = environment == Environment.PRODUCTION if raw_cookie_secure is None else raw_cookie_secure.strip().lower() in {"1", "true", "yes"}
    try:
        session_lifetime_hours = int(os.getenv("AUTH_SESSION_HOURS", "12"))
    except ValueError as error:
        raise RuntimeError("AUTH_SESSION_HOURS deve ser inteiro.") from error

    settings = ApiSettings(
        environment=environment,
        cors_origins=origins,
        session_cookie_name=os.getenv("AUTH_COOKIE_NAME", "aurora_session").strip(),
        session_lifetime_hours=session_lifetime_hours,
        cookie_secure=cookie_secure,
    )
    settings.validate()
    return settings
