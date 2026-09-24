"""Schemas HTTP de Transactions e Settlements."""

from datetime import date, datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from api.schemas.accounts import parse_canonical_money
from models import DerivedTransactionStatus, TransactionStatus, TransactionType
from services import DatePerspective


def money_string(value: Decimal) -> str:
    return format(value, ".2f")


def aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        # SQLite perde o offset. Valores gravados pela API são normalizados em UTC.
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class MoneyInputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @staticmethod
    def parse_money(value: object) -> Decimal:
        return parse_canonical_money(value)


class TransactionCreate(MoneyInputModel):
    transaction_type: TransactionType
    description: str
    amount: Decimal
    competence_date: date
    due_date: date | None = None
    category_id: int
    subcategory_id: int | None = None
    notes: str | None = None

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value: object) -> Decimal:
        return cls.parse_money(value)


class SettlementCreate(MoneyInputModel):
    account_id: int
    amount: Decimal
    settled_at: datetime
    notes: str | None = None

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value: object) -> Decimal:
        return cls.parse_money(value)

    @field_validator("settled_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("settled_at deve possuir timezone/offset.")
        return value.astimezone(timezone.utc)


class SettledTransactionCreate(MoneyInputModel):
    transaction_type: TransactionType
    description: str
    amount: Decimal
    competence_date: date
    due_date: date | None = None
    category_id: int
    subcategory_id: int | None = None
    transaction_notes: str | None = None
    settlement: SettlementCreate

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value: object) -> Decimal:
        return cls.parse_money(value)

    @model_validator(mode="after")
    def require_integral_settlement(self):
        if self.settlement.amount != self.amount:
            raise ValueError(
                "A criação histórica exige Settlement integral igual ao amount."
            )
        return self


class CancellationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = None


class NamedReference(BaseModel):
    id: int
    name: str


class SettlementResponse(BaseModel):
    id: int
    account: NamedReference
    amount: str
    settled_at: datetime
    notes: str | None


class CancellationResponse(BaseModel):
    cancelled_at: datetime
    reason: str | None


class TransactionListItemResponse(BaseModel):
    id: int
    transaction_type: TransactionType
    derived_status: DerivedTransactionStatus
    description: str
    amount: str
    settled_amount: str
    remaining_amount: str
    period_settled_amount: str
    competence_date: date
    due_date: date | None
    reference_date: date
    category: NamedReference
    subcategory: NamedReference | None


class TransactionDetailResponse(BaseModel):
    id: int
    transaction_type: TransactionType
    persisted_status: TransactionStatus
    derived_status: DerivedTransactionStatus
    description: str
    amount: str
    settled_amount: str
    remaining_amount: str
    competence_date: date
    due_date: date | None
    category: NamedReference
    subcategory: NamedReference | None
    notes: str | None
    cancellation: CancellationResponse | None
    settlements: list[SettlementResponse]


class PaginationResponse(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class TransactionPageResponse(BaseModel):
    items: list[TransactionListItemResponse]
    pagination: PaginationResponse


class TransactionQueryParams(BaseModel):
    perspective: DatePerspective = DatePerspective.COMPETENCE
    start_date: date
    end_date: date
    transaction_type: TransactionType | None = None
    derived_status: DerivedTransactionStatus | None = None
    category_id: int | None = None
    subcategory_id: int | None = None
    search: str = ""
    include_cancelled: bool = False
    page: int = 1
    page_size: int = 25

    @model_validator(mode="after")
    def validate_period(self):
        if self.start_date > self.end_date:
            raise ValueError("start_date não pode ser posterior a end_date.")
        return self
