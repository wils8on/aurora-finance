"""Tradução de exceptions internas para o contrato HTTP."""

from decimal import Decimal
from datetime import date, datetime
from enum import Enum
import logging
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from services import (
    ApplicationError,
    ConflictError,
    NotFoundError,
    OwnershipError,
    ValidationError,
)

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid4()))


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Exception):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    field: str | None = None,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "field": field,
                "details": _json_safe(details or {}),
                "request_id": _request_id(request),
            }
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApplicationError)
    async def application_error_handler(
        request: Request, error: ApplicationError
    ) -> JSONResponse:
        if isinstance(error, ValidationError):
            status_code = 422
        elif isinstance(error, (NotFoundError, OwnershipError)):
            status_code = 404
        elif isinstance(error, ConflictError):
            status_code = 409
        else:
            status_code = 500
        return _error_response(
            request,
            status_code=status_code,
            code=error.code,
            message=error.message,
            field=error.field,
            details=error.details,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        errors = error.errors()
        first = errors[0] if errors else {}
        location = first.get("loc", ())
        field = str(location[-1]) if location else None
        safe_errors = [
            {
                "type": item.get("type"),
                "loc": list(item.get("loc", ())),
                "message": item.get("msg"),
            }
            for item in errors
        ]
        return _error_response(
            request,
            status_code=422,
            code="REQUEST_VALIDATION_ERROR",
            message="Payload ou parâmetros inválidos.",
            field=field,
            details={"errors": safe_errors},
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(
        request: Request, _error: Exception
    ) -> JSONResponse:
        logger.exception(
            "Erro inesperado na API. request_id=%s",
            _request_id(request),
            exc_info=_error,
        )
        return _error_response(
            request,
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
            message="Ocorreu um erro inesperado.",
        )
