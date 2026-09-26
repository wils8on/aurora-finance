"""Testes da camada de leitura usada pela interface."""

from datetime import date, datetime, time, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from components.finance import due_condition
from models import (
    Account,
    AccountType,
    Category,
    CategoryType,
    DerivedTransactionStatus,
    TransactionType,
    User,
)
from services import DatePerspective, TransactionFilters, TransactionQueryService, TransactionService
from utils.formatting import format_currency, format_date, format_datetime, localize_datetime, parse_decimal

SEPTEMBER_START = date(2026, 9, 1)
SEPTEMBER_END = date(2026, 9, 30)


@pytest.fixture
def query_context(session: Session):
    user = User(name="Aurora", email="query@example.com")
    income = Category(user=user, name="Trabalho", type=CategoryType.INCOME)
    expense = Category(user=user, name="Moradia", type=CategoryType.EXPENSE)
    account = Account(
        user=user,
        name="Conta principal",
        account_type=AccountType.CHECKING,
        initial_balance=Decimal("0.00"),
    )
    session.add(user)
    session.commit()
    return user, income, expense, account, TransactionService(session)


def filters(user_id: int, **changes) -> TransactionFilters:
    values = {
        "user_id": user_id,
        "start_date": SEPTEMBER_START,
        "end_date": SEPTEMBER_END,
    }
    values.update(changes)
    return TransactionFilters(**values)


def test_competence_filter_and_summary(session, query_context) -> None:
    user, income, expense, _account, service = query_context
    service.create_transaction(
        user_id=user.id,
        category_id=income.id,
        transaction_type=TransactionType.INCOME,
        description="Salário setembro",
        amount=Decimal("5000.00"),
        competence_date=date(2026, 9, 5),
    )
    service.create_transaction(
        user_id=user.id,
        category_id=expense.id,
        transaction_type=TransactionType.EXPENSE,
        description="Aluguel setembro",
        amount=Decimal("1200.00"),
        competence_date=date(2026, 9, 1),
    )
    service.create_transaction(
        user_id=user.id,
        category_id=expense.id,
        transaction_type=TransactionType.EXPENSE,
        description="Fora do período",
        amount=Decimal("100.00"),
        competence_date=date(2026, 10, 1),
    )
    query = TransactionQueryService(session)
    result = query.list_transactions(filters(user.id))
    summary = query.summarize(filters(user.id))
    assert result.total == 2
    assert summary.primary_1 == Decimal("5000.00")
    assert summary.primary_2 == Decimal("1200.00")
    assert summary.primary_3 == Decimal("3800.00")
    assert summary.receivable == Decimal("5000.00")
    assert summary.payable == Decimal("1200.00")


def test_search_type_state_and_category_filters(session, query_context) -> None:
    user, income, expense, _account, service = query_context
    income_tx = service.create_transaction(
        user_id=user.id,
        category_id=income.id,
        transaction_type=TransactionType.INCOME,
        description="Consultoria especial",
        amount=Decimal("300.00"),
        competence_date=date(2026, 9, 10),
    )
    service.create_transaction(
        user_id=user.id,
        category_id=expense.id,
        transaction_type=TransactionType.EXPENSE,
        description="Energia",
        amount=Decimal("200.00"),
        competence_date=date(2026, 9, 10),
    )
    query = TransactionQueryService(session)
    result = query.list_transactions(
        filters(
            user.id,
            search="trabalho",
            transaction_type=TransactionType.INCOME,
            derived_status=DerivedTransactionStatus.PENDING,
            category_id=income.id,
        )
    )
    assert [item.id for item in result.items] == [income_tx.id]


def test_pagination_does_not_load_entire_history(session, query_context) -> None:
    user, _income, expense, _account, service = query_context
    for number in range(30):
        service.create_transaction(
            user_id=user.id,
            category_id=expense.id,
            transaction_type=TransactionType.EXPENSE,
            description=f"Despesa {number}",
            amount=Decimal("10.00"),
            competence_date=date(2026, 9, 10),
        )
    result = TransactionQueryService(session).list_transactions(filters(user.id, page_size=25))
    assert result.total == 30
    assert len(result.items) == 25
    assert result.pages == 2


def test_due_perspective_and_overdue_indicator(session, query_context) -> None:
    user, _income, expense, _account, service = query_context
    service.create_transaction(
        user_id=user.id,
        category_id=expense.id,
        transaction_type=TransactionType.EXPENSE,
        description="Vencida",
        amount=Decimal("80.00"),
        competence_date=date(2026, 8, 1),
        due_date=date(2026, 9, 1),
    )
    query_filters = filters(user.id, perspective=DatePerspective.DUE)
    query = TransactionQueryService(session)
    result = query.list_transactions(query_filters)
    summary = query.summarize(query_filters)
    assert result.total == 1
    assert summary.primary_2 == Decimal("80.00")
    assert summary.primary_3 == Decimal("80.00")


def test_cash_perspective_uses_only_settlements_in_period(session, query_context) -> None:
    user, income, _expense, account, service = query_context
    transaction = service.create_transaction(
        user_id=user.id,
        category_id=income.id,
        transaction_type=TransactionType.INCOME,
        description="Recebimento parcial",
        amount=Decimal("500.00"),
        competence_date=date(2026, 8, 1),
    )
    service.add_settlement(
        transaction_id=transaction.id,
        user_id=user.id,
        account_id=account.id,
        amount=Decimal("200.00"),
        settled_at=datetime(2026, 9, 15, 10, tzinfo=timezone.utc),
    )
    service.add_settlement(
        transaction_id=transaction.id,
        user_id=user.id,
        account_id=account.id,
        amount=Decimal("100.00"),
        settled_at=datetime(2026, 10, 1, 10, tzinfo=timezone.utc),
    )
    query_filters = filters(user.id, perspective=DatePerspective.CASH)
    query = TransactionQueryService(session)
    result = query.list_transactions(query_filters)
    summary = query.summarize(query_filters)
    assert result.total == 1
    assert result.items[0].settled_amount == Decimal("300.00")
    assert result.items[0].period_settled_amount == Decimal("200.00")
    assert summary.primary_1 == Decimal("200.00")
    assert summary.primary_3 == Decimal("200.00")


def test_cash_boundary_instant_belongs_only_to_previous_operational_day(
    session, query_context
) -> None:
    user, income, _expense, account, service = query_context
    transaction = service.create_transaction(
        user_id=user.id,
        category_id=income.id,
        transaction_type=TransactionType.INCOME,
        description="Receita 22 às 23h30",
        amount=Decimal("100.00"),
        competence_date=date(2026, 9, 22),
    )
    service.add_settlement(
        transaction_id=transaction.id,
        user_id=user.id,
        account_id=account.id,
        amount=Decimal("100.00"),
        settled_at=datetime(2026, 9, 23, 2, 30, tzinfo=timezone.utc),
    )
    query = TransactionQueryService(session)
    previous_day = filters(
        user.id, perspective=DatePerspective.CASH,
        start_date=date(2026, 9, 22), end_date=date(2026, 9, 22),
    )
    utc_day = filters(
        user.id, perspective=DatePerspective.CASH,
        start_date=date(2026, 9, 23), end_date=date(2026, 9, 23),
    )
    result = query.list_transactions(previous_day)
    assert result.total == 1
    assert result.items[0].reference_date == date(2026, 9, 22)
    assert query.list_transactions(utc_day).total == 0
    assert query.summarize(utc_day).primary_1 == Decimal("0.00")


def test_cash_uses_operational_day_for_filters_reference_and_multiple_settlements(
    session, query_context
) -> None:
    user, income, expense, account, service = query_context
    received = service.create_transaction(
        user_id=user.id,
        category_id=income.id,
        transaction_type=TransactionType.INCOME,
        description="Receita na virada UTC",
        amount=Decimal("300.00"),
        competence_date=date(2026, 9, 1),
    )
    paid = service.create_transaction(
        user_id=user.id,
        category_id=expense.id,
        transaction_type=TransactionType.EXPENSE,
        description="Despesa na virada UTC",
        amount=Decimal("100.00"),
        competence_date=date(2026, 9, 1),
    )
    for transaction, amount, instant in (
        (received, Decimal("100.00"), datetime(2026, 9, 23, 2, 30, tzinfo=timezone.utc)),
        (received, Decimal("200.00"), datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)),
        (paid, Decimal("40.00"), datetime(2026, 9, 23, 2, 45, tzinfo=timezone.utc)),
        (paid, Decimal("60.00"), datetime(2026, 9, 23, 14, 0, tzinfo=timezone.utc)),
    ):
        service.add_settlement(
            transaction_id=transaction.id,
            user_id=user.id,
            account_id=account.id,
            amount=amount,
            settled_at=instant,
        )

    query = TransactionQueryService(session)
    day_22 = filters(
        user.id,
        perspective=DatePerspective.CASH,
        start_date=date(2026, 9, 22),
        end_date=date(2026, 9, 22),
    )
    result_22 = query.list_transactions(day_22)
    summary_22 = query.summarize(day_22)
    assert result_22.total == 2
    assert {item.reference_date for item in result_22.items} == {date(2026, 9, 22)}
    assert {item.id: item.period_settled_amount for item in result_22.items} == {
        received.id: Decimal("100.00"), paid.id: Decimal("40.00")
    }
    assert {item.id: item.settled_amount for item in result_22.items} == {
        received.id: Decimal("300.00"), paid.id: Decimal("100.00")
    }
    assert (summary_22.primary_1, summary_22.primary_2, summary_22.primary_3) == (
        Decimal("100.00"), Decimal("40.00"), Decimal("60.00")
    )

    day_23 = filters(
        user.id,
        perspective=DatePerspective.CASH,
        start_date=date(2026, 9, 23),
        end_date=date(2026, 9, 23),
    )
    result_23 = query.list_transactions(day_23)
    summary_23 = query.summarize(day_23)
    assert result_23.total == 2
    assert {item.reference_date for item in result_23.items} == {date(2026, 9, 23)}
    assert {item.id: item.period_settled_amount for item in result_23.items} == {
        received.id: Decimal("200.00"), paid.id: Decimal("60.00")
    }
    assert (summary_23.primary_1, summary_23.primary_2, summary_23.primary_3) == (
        Decimal("200.00"), Decimal("60.00"), Decimal("140.00")
    )


def test_cancelled_hidden_by_default_and_available_by_filter(session, query_context) -> None:
    user, _income, expense, _account, service = query_context
    transaction = service.create_transaction(
        user_id=user.id,
        category_id=expense.id,
        transaction_type=TransactionType.EXPENSE,
        description="Cancelada",
        amount=Decimal("50.00"),
        competence_date=date(2026, 9, 10),
    )
    service.cancel_transaction(transaction_id=transaction.id, user_id=user.id)
    query = TransactionQueryService(session)
    assert query.list_transactions(filters(user.id)).total == 0
    cancelled = query.list_transactions(
        filters(
            user.id,
            derived_status=DerivedTransactionStatus.CANCELLED,
            include_cancelled=True,
        )
    )
    assert cancelled.total == 1


@pytest.mark.parametrize(
    ("source", "expected"),
    [("1234.56", Decimal("1234.56")), ("1.234,56", Decimal("1234.56")), ("0,01", Decimal("0.01"))],
)
def test_safe_decimal_conversion(source, expected) -> None:
    assert parse_decimal(source) == expected


def test_decimal_conversion_rejects_more_than_two_places() -> None:
    with pytest.raises(ValueError, match="duas casas"):
        parse_decimal("1,001")


def test_pt_br_formatting() -> None:
    assert format_currency(Decimal("1234.56")) == "R$ 1.234,56"
    assert format_date(date(2026, 9, 23)) == "23/09/2026"


def test_sao_paulo_timezone_conversion() -> None:
    value = localize_datetime(date(2026, 9, 23), time(14, 30))
    assert value.tzinfo is not None
    assert value.utcoffset().total_seconds() == -3 * 60 * 60
    assert format_datetime(value) == "23/09/2026 14:30"


def test_due_condition_is_derived_and_textual() -> None:
    assert due_condition(
        date(2026, 9, 20),
        DerivedTransactionStatus.PARTIAL,
        Decimal("10.00"),
        today=date(2026, 9, 23),
    ) == "⚠ Vencida há 3 dias"
    assert due_condition(
        date(2026, 9, 20),
        DerivedTransactionStatus.SETTLED,
        Decimal("0.00"),
        today=date(2026, 9, 23),
    ) == ""
