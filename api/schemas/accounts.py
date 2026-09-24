"""Schemas HTTP de contas."""

from datetime import date
from decimal import Decimal, InvalidOperation
import re

from pydantic import BaseModel, ConfigDict, field_validator

from models import AccountType

CANONICAL_MONEY = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d{1,2})?$")


class AccountCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    institution: str | None = None
    account_type: AccountType
    initial_balance: Decimal
    initial_balance_date: date | None = None

    @field_validator("initial_balance", mode="before")
    @classmethod
    def validate_money_string(cls, value: object) -> Decimal:
        if not isinstance(value, str) or not CANONICAL_MONEY.fullmatch(value):
            raise ValueError("Use string decimal canônica, por exemplo: 1234.56.")
        try:
            amount = Decimal(value)
        except InvalidOperation as error:
            raise ValueError("Valor monetário inválido.") from error
        if not amount.is_finite():
            raise ValueError("Valor monetário inválido.")
        return amount


class AccountResponse(BaseModel):
    id: int
    name: str
    institution: str | None
    account_type: AccountType
    initial_balance: str
    initial_balance_date: date | None
    is_active: bool
