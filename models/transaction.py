"""Modelo da dimensão econômica de receitas e despesas."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base
from models.enums import TransactionStatus, TransactionType
from models.mixins import TimestampMixin


class Transaction(TimestampMixin, Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint(
            "(status = 'ACTIVE' AND cancelled_at IS NULL AND cancellation_reason IS NULL) "
            "OR (status = 'CANCELLED' AND cancelled_at IS NOT NULL)",
            name="cancellation_state_consistent",
        ),
        Index("ix_transactions_user_status_due_date", "user_id", "status", "due_date"),
        Index("ix_transactions_user_competence_date", "user_id", "competence_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    subcategory_id: Mapped[int | None] = mapped_column(
        ForeignKey("subcategories.id", ondelete="RESTRICT"), index=True
    )
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(
            TransactionType,
            name="transaction_type",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
    )
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(
            TransactionStatus,
            name="transaction_status",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
        default=TransactionStatus.ACTIVE,
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    competence_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="transactions")
    category: Mapped["Category"] = relationship(back_populates="transactions")
    subcategory: Mapped["Subcategory | None"] = relationship(back_populates="transactions")
    settlements: Mapped[list["Settlement"]] = relationship(
        back_populates="transaction", passive_deletes=True
    )
