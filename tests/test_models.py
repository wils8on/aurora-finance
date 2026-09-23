"""Testes dos modelos fundamentais e seus relacionamentos."""

from datetime import date
from decimal import Decimal

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from models import Account, AccountType, Category, CategoryType, Subcategory, User


def test_database_initialization(test_engine) -> None:
    assert set(inspect(test_engine).get_table_names()) == {
        "accounts",
        "categories",
        "subcategories",
        "users",
    }


def test_create_user(session: Session) -> None:
    user = User(name="Aurora", email="aurora@example.com")
    session.add(user)
    session.commit()

    assert user.id is not None
    assert user.currency == "BRL"
    assert user.is_active is True
    assert user.created_at is not None
    assert user.updated_at is not None


def test_create_account_and_user_relationship(session: Session) -> None:
    user = User(name="Aurora", email="conta@example.com")
    account = Account(
        user=user,
        name="Conta principal",
        institution="Banco exemplo",
        account_type=AccountType.CHECKING,
        initial_balance=Decimal("1250.45"),
        initial_balance_date=date(2026, 1, 1),
    )
    session.add(account)
    session.commit()

    assert account.id is not None
    assert account.user is user
    assert user.accounts == [account]
    assert account.initial_balance == Decimal("1250.45")


def test_create_category_and_subcategory_relationship(session: Session) -> None:
    user = User(name="Aurora", email="categoria@example.com")
    category = Category(user=user, name="Alimentação", type=CategoryType.EXPENSE)
    subcategory = Subcategory(category=category, name="Supermercado")
    session.add(subcategory)
    session.commit()

    assert category.id is not None
    assert subcategory.id is not None
    assert category.user is user
    assert user.categories == [category]
    assert category.subcategories == [subcategory]
    assert subcategory.category is category
