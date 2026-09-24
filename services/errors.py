"""Erros classificáveis da camada de aplicação, sem dependência de transporte."""

from collections.abc import Mapping
from typing import Any


class ApplicationError(ValueError):
    """Erro esperado da aplicação com metadados estáveis para adaptadores."""

    default_code = "APPLICATION_ERROR"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        field: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code or self.default_code
        self.message = message
        self.field = field
        self.details = dict(details or {})


class ValidationError(ApplicationError):
    """Entrada ausente, malformada ou semanticamente inválida."""

    default_code = "VALIDATION_ERROR"


class NotFoundError(ApplicationError):
    """Recurso esperado não encontrado."""

    default_code = "RESOURCE_NOT_FOUND"


class ConflictError(ApplicationError):
    """Operação incompatível com o estado atual do recurso."""

    default_code = "CONFLICT"


class OwnershipError(ApplicationError):
    """Recurso não pertence ao usuário que executa a operação."""

    default_code = "RESOURCE_OWNERSHIP_MISMATCH"
