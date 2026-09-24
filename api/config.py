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
    dev_user_email: str | None
    api_prefix: str = API_PREFIX

    def validate(self) -> None:
        if "*" in self.cors_origins:
            raise RuntimeError("CORS wildcard não é permitido.")
        if self.environment == Environment.PRODUCTION:
            raise RuntimeError(
                "A API não pode iniciar em produção sem autenticação suportada."
            )


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
    dev_user_email = os.getenv("AURORA_DEV_USER_EMAIL")
    if dev_user_email:
        dev_user_email = dev_user_email.strip() or None

    settings = ApiSettings(
        environment=environment,
        cors_origins=origins,
        dev_user_email=dev_user_email,
    )
    settings.validate()
    return settings
