"""Testes das regras de Transaction e Settlement."""

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import (
    Account,
    AccountType,
    Category,
    CategoryType,
    DerivedTransactionStatus,
    Settlement,
    Subcategory,
    Transaction,
    TransactionStatus,
    TransactionType,
    User,
)
from services import TransactionService, TransactionServiceError

TODAY = date(2026, 9, 23)
NOW = datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def context(session: Session) -> SimpleNamespace:
    user = User(name="Aurora", email="financeiro@example.com")
    other_user = User(name="Outro", email="outro@example.com")
    income = Category(user=user, name="Salário", type=CategoryType.INCOME)
    expense = Category(user=user, name="Moradia", type=CategoryType.EXPENSE)
    other_expense = Category(user=other_user, name="Outras", type=CategoryType.EXPENSE)
    rent = Subcategory(category=expense, name="Aluguel")
    other_subcategory = Subcategory(category=other_expense, name="Externa")
    account = Account(
        user=user,
        name="Conta principal",
        account_type=AccountType.CHECKING,
        initial_balance=Decimal("0.00"),
    )
    other_account = Account(
        user=other_user,
        name="Conta externa",
        account_type=AccountType.CHECKING,
        initial_balance=Decimal("0.00"),
    )
    session.add_all([user, other_user])
    session.commit()
    return SimpleNamespace(
        user=user,
        other_user=other_user,
        income=income,
        expense=expense,
        other_expense=other_expense,
        rent=rent,
        other_subcategory=other_subcategory,
        account=account,
        other_account=other_account,
        service=TransactionService(session),
    )


def create_expense(context, amount: Decimal = Decimal("100.00")) -> Transaction:
    return context.service.create_transaction(
        user_id=context.user.id,
        category_id=context.expense.id,
        subcategory_id=context.rent.id,
        transaction_type=TransactionType.EXPENSE,
        description="Aluguel",
        amount=amount,
        competence_date=TODAY,
    )


def test_create_pending_income(context) -> None:
    transaction = context.service.create_transaction(
        user_id=context.user.id,
        category_id=context.income.id,
        transaction_type=TransactionType.INCOME,
        description="Salário",
        amount=Decimal("5000.00"),
        competence_date=TODAY,
    )
    assert transaction.status == TransactionStatus.ACTIVE
    assert context.service.get_derived_status(transaction.id, context.user.id) == DerivedTransactionStatus.PENDING


def test_create_pending_expense(context) -> None:
    transaction = create_expense(context)
    assert transaction.transaction_type == TransactionType.EXPENSE
    assert transaction.amount == Decimal("100.00")


def test_transaction_without_settlement_is_pending(context) -> None:
    transaction = create_expense(context)
    assert context.service.get_settled_amount(transaction.id, context.user.id) == Decimal("0.00")
    assert context.service.get_derived_status(transaction.id, context.user.id) == DerivedTransactionStatus.PENDING


def test_partial_settlement(context) -> None:
    transaction = create_expense(context)
    context.service.add_settlement(
        transaction_id=transaction.id,
        user_id=context.user.id,
        account_id=context.account.id,
        amount=Decimal("40.00"),
        settled_at=NOW,
    )
    assert context.service.get_derived_status(transaction.id, context.user.id) == DerivedTransactionStatus.PARTIAL
    assert context.service.get_remaining_amount(transaction.id, context.user.id) == Decimal("60.00")


def test_complete_settlement(context) -> None:
    transaction = create_expense(context)
    context.service.add_settlement(
        transaction_id=transaction.id,
        user_id=context.user.id,
        account_id=context.account.id,
        amount=Decimal("100.00"),
        settled_at=NOW,
    )
    assert context.service.get_derived_status(transaction.id, context.user.id) == DerivedTransactionStatus.SETTLED
    assert context.service.get_remaining_amount(transaction.id, context.user.id) == Decimal("0.00")


def test_multiple_settlements_and_derived_amounts(context) -> None:
    transaction = create_expense(context)
    for amount in (Decimal("25.00"), Decimal("35.00"), Decimal("40.00")):
        context.service.add_settlement(
            transaction_id=transaction.id,
            user_id=context.user.id,
            account_id=context.account.id,
            amount=amount,
            settled_at=NOW,
        )
    assert context.service.get_settled_amount(transaction.id, context.user.id) == Decimal("100.00")
    assert len(transaction.settlements) == 3


def test_reject_settlement_above_nominal_amount(context) -> None:
    transaction = create_expense(context)
    with pytest.raises(TransactionServiceError, match="exceder"):
        context.service.add_settlement(
            transaction_id=transaction.id,
            user_id=context.user.id,
            account_id=context.account.id,
            amount=Decimal("100.01"),
            settled_at=NOW,
        )


def test_cancel_transaction_without_settlement(context) -> None:
    transaction = create_expense(context)
    context.service.cancel_transaction(
        transaction_id=transaction.id,
        user_id=context.user.id,
        cancellation_reason="Cobrança removida",
        cancelled_at=NOW,
    )
    assert transaction.status == TransactionStatus.CANCELLED
    assert transaction.cancelled_at == NOW
    assert context.service.get_derived_status(transaction.id, context.user.id) == DerivedTransactionStatus.CANCELLED


def test_reject_settlement_on_cancelled_transaction(context) -> None:
    transaction = create_expense(context)
    context.service.cancel_transaction(transaction_id=transaction.id, user_id=context.user.id)
    with pytest.raises(TransactionServiceError, match="cancelada"):
        context.service.add_settlement(
            transaction_id=transaction.id,
            user_id=context.user.id,
            account_id=context.account.id,
            amount=Decimal("10.00"),
            settled_at=NOW,
        )


def test_reject_cancellation_with_settlement(context) -> None:
    transaction = create_expense(context)
    context.service.add_settlement(
        transaction_id=transaction.id,
        user_id=context.user.id,
        account_id=context.account.id,
        amount=Decimal("10.00"),
        settled_at=NOW,
    )
    with pytest.raises(TransactionServiceError, match="não pode ser cancelada"):
        context.service.cancel_transaction(transaction_id=transaction.id, user_id=context.user.id)


def test_create_historical_transaction_and_settlement(context) -> None:
    transaction, settlement = context.service.create_settled_historical_transaction(
        user_id=context.user.id,
        category_id=context.expense.id,
        account_id=context.account.id,
        transaction_type=TransactionType.EXPENSE,
        description="Despesa histórica",
        amount=Decimal("125.00"),
        competence_date=TODAY,
        settled_at=NOW,
    )
    assert settlement.transaction_id == transaction.id
    assert settlement.amount == Decimal("125.00")
    assert context.service.get_derived_status(transaction.id, context.user.id) == DerivedTransactionStatus.SETTLED


def test_historical_creation_rolls_back_if_settlement_fails(context, session, monkeypatch) -> None:
    def fail_to_add(_settlement) -> None:
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(context.service.settlements, "add", fail_to_add)
    with pytest.raises(RuntimeError, match="falha simulada"):
        context.service.create_settled_historical_transaction(
            user_id=context.user.id,
            category_id=context.expense.id,
            account_id=context.account.id,
            transaction_type=TransactionType.EXPENSE,
            description="Não deve persistir",
            amount=Decimal("125.00"),
            competence_date=TODAY,
            settled_at=NOW,
        )
    assert session.scalar(select(func.count(Transaction.id))) == 0


def test_reject_category_incompatible_with_transaction_type(context) -> None:
    with pytest.raises(TransactionServiceError, match="incompatível"):
        context.service.create_transaction(
            user_id=context.user.id,
            category_id=context.expense.id,
            transaction_type=TransactionType.INCOME,
            description="Inválida",
            amount=Decimal("10.00"),
            competence_date=TODAY,
        )


def test_reject_subcategory_from_another_category(context) -> None:
    with pytest.raises(TransactionServiceError, match="Subcategory"):
        context.service.create_transaction(
            user_id=context.user.id,
            category_id=context.expense.id,
            subcategory_id=context.other_subcategory.id,
            transaction_type=TransactionType.EXPENSE,
            description="Inválida",
            amount=Decimal("10.00"),
            competence_date=TODAY,
        )


def test_reject_entities_from_another_user(context) -> None:
    with pytest.raises(TransactionServiceError, match="Category"):
        context.service.create_transaction(
            user_id=context.user.id,
            category_id=context.other_expense.id,
            transaction_type=TransactionType.EXPENSE,
            description="Inválida",
            amount=Decimal("10.00"),
            competence_date=TODAY,
        )
    transaction = create_expense(context)
    with pytest.raises(TransactionServiceError, match="Account"):
        context.service.add_settlement(
            transaction_id=transaction.id,
            user_id=context.user.id,
            account_id=context.other_account.id,
            amount=Decimal("10.00"),
            settled_at=NOW,
        )


def test_reject_transaction_access_from_another_user(context) -> None:
    transaction = create_expense(context)
    with pytest.raises(TransactionServiceError, match="Transaction"):
        context.service.get_settled_amount(transaction.id, context.other_user.id)


def test_money_requires_decimal(context) -> None:
    with pytest.raises(TransactionServiceError, match="Decimal"):
        context.service.create_transaction(
            user_id=context.user.id,
            category_id=context.expense.id,
            transaction_type=TransactionType.EXPENSE,
            description="Inválida",
            amount=10.0,  # type: ignore[arg-type]
            competence_date=TODAY,
        )


def test_transaction_positive_amount_database_constraint(context, session) -> None:
    transaction = Transaction(
        user_id=context.user.id,
        category_id=context.expense.id,
        transaction_type=TransactionType.EXPENSE,
        status=TransactionStatus.ACTIVE,
        description="Inválida",
        amount=Decimal("0.00"),
        competence_date=TODAY,
    )
    session.add(transaction)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_settlement_positive_amount_database_constraint(context, session) -> None:
    transaction = create_expense(context)
    settlement = Settlement(
        transaction_id=transaction.id,
        account_id=context.account.id,
        amount=Decimal("0.00"),
        settled_at=NOW,
    )
    session.add(settlement)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_transaction_settlement_relationship(context, session) -> None:
    transaction = create_expense(context)
    settlement = context.service.add_settlement(
        transaction_id=transaction.id,
        user_id=context.user.id,
        account_id=context.account.id,
        amount=Decimal("10.00"),
        settled_at=NOW,
    )
    session.expire_all()
    loaded = session.get(Transaction, transaction.id)
    assert loaded is not None
    assert loaded.settlements == [settlement]
    assert settlement.account.settlements == [settlement]


def test_financial_deletion_is_restricted(context, session) -> None:
    transaction = create_expense(context)
    context.service.add_settlement(
        transaction_id=transaction.id,
        user_id=context.user.id,
        account_id=context.account.id,
        amount=Decimal("10.00"),
        settled_at=NOW,
    )
    session.commit()
    with pytest.raises(IntegrityError):
        session.execute(delete(Transaction).where(Transaction.id == transaction.id))
        session.commit()
    session.rollback()
