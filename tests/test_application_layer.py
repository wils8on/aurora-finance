"""Testes dos contratos internos preparados para futuros adaptadores."""

import ast
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from models import Account, AccountType, Category, CategoryType, TransactionType, User
from services import (
    ApplicationError,
    ConflictError,
    DatePerspective,
    FixedClock,
    SystemClock,
    TransactionFilters,
    TransactionQueryService,
    TransactionService,
)
from services.clock import OPERATIONAL_TIMEZONE
from utils.money import parse_decimal


def test_application_error_exposes_stable_metadata() -> None:
    error = ConflictError(
        "Conflito financeiro.",
        code="FINANCIAL_CONFLICT",
        field="amount",
        details={"remaining_amount": Decimal("10.00")},
    )

    assert isinstance(error, ApplicationError)
    assert str(error) == "Conflito financeiro."
    assert error.code == "FINANCIAL_CONFLICT"
    assert error.field == "amount"
    assert error.details == {"remaining_amount": Decimal("10.00")}


def test_settlement_excess_has_code_field_and_details(session) -> None:
    user = User(name="Aurora", email="errors@example.com")
    category = Category(user=user, name="Moradia", type=CategoryType.EXPENSE)
    account = Account(
        user=user,
        name="Conta",
        account_type=AccountType.CHECKING,
        initial_balance=Decimal("0.00"),
    )
    session.add(user)
    session.flush()
    service = TransactionService(session)
    transaction = service.create_transaction(
        user_id=user.id,
        category_id=category.id,
        transaction_type=TransactionType.EXPENSE,
        description="Aluguel",
        amount=Decimal("100.00"),
        competence_date=date(2026, 9, 1),
    )

    with pytest.raises(ConflictError) as captured:
        service.add_settlement(
            transaction_id=transaction.id,
            user_id=user.id,
            account_id=account.id,
            amount=Decimal("100.01"),
            settled_at=datetime(2026, 9, 23, 12, tzinfo=timezone.utc),
        )

    assert captured.value.code == "SETTLEMENT_EXCEEDS_REMAINING_AMOUNT"
    assert captured.value.field == "amount"
    assert captured.value.details == {"remaining_amount": Decimal("100.00")}


def test_system_clock_is_timezone_aware_in_sao_paulo() -> None:
    current = SystemClock().now()

    assert current.tzinfo is not None
    assert current.utcoffset() is not None
    assert current.tzinfo == OPERATIONAL_TIMEZONE
    assert SystemClock().today() == datetime.now(OPERATIONAL_TIMEZONE).date()


def test_fixed_clock_normalizes_instant_and_exposes_operational_date() -> None:
    clock = FixedClock(datetime(2026, 9, 24, 1, 30, tzinfo=timezone.utc))

    assert clock.now().isoformat() == "2026-09-23T22:30:00-03:00"
    assert clock.today() == date(2026, 9, 23)


def test_fixed_clock_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        FixedClock(datetime(2026, 9, 23, 12))


def test_transaction_cancellation_uses_injected_clock(session) -> None:
    fixed_now = datetime(2026, 9, 23, 14, 30, tzinfo=OPERATIONAL_TIMEZONE)
    clock = FixedClock(fixed_now)
    user = User(name="Aurora", email="clock@example.com")
    category = Category(user=user, name="Moradia", type=CategoryType.EXPENSE)
    session.add(user)
    session.flush()
    service = TransactionService(session, clock=clock)
    transaction = service.create_transaction(
        user_id=user.id,
        category_id=category.id,
        transaction_type=TransactionType.EXPENSE,
        description="Aluguel",
        amount=Decimal("100.00"),
        competence_date=date(2026, 9, 1),
    )

    service.cancel_transaction(transaction_id=transaction.id, user_id=user.id)

    assert transaction.cancelled_at == fixed_now


def test_due_summary_uses_injected_clock_and_changes_with_date(session) -> None:
    user = User(name="Aurora", email="due-clock@example.com")
    category = Category(user=user, name="Moradia", type=CategoryType.EXPENSE)
    session.add(user)
    session.flush()
    service = TransactionService(session)
    service.create_transaction(
        user_id=user.id,
        category_id=category.id,
        transaction_type=TransactionType.EXPENSE,
        description="Conta",
        amount=Decimal("80.00"),
        competence_date=date(2026, 9, 1),
        due_date=date(2026, 9, 23),
    )
    filters = TransactionFilters(
        user_id=user.id,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
        perspective=DatePerspective.DUE,
    )

    on_due_date = TransactionQueryService(
        session,
        clock=FixedClock(datetime(2026, 9, 23, 12, tzinfo=OPERATIONAL_TIMEZONE)),
    ).summarize(filters)
    after_due_date = TransactionQueryService(
        session,
        clock=FixedClock(datetime(2026, 9, 24, 12, tzinfo=OPERATIONAL_TIMEZONE)),
    ).summarize(filters)

    assert on_due_date.primary_3 == Decimal("0.00")
    assert after_due_date.primary_3 == Decimal("80.00")


def test_query_service_has_no_presentation_framework_import() -> None:
    source = Path("services/query_service.py").read_text(encoding="utf-8")
    imports = {
        node.names[0].name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Import)
    }
    imports.update(
        node.module
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom) and node.module
    )

    assert all(not name.startswith("streamlit") for name in imports)


def test_money_parser_is_independent_and_preserves_decimal() -> None:
    result = parse_decimal("1.234,56")

    assert result == Decimal("1234.56")
    assert isinstance(result, Decimal)
