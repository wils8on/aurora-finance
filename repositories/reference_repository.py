"""Consultas simples das entidades referenciadas pelo núcleo financeiro."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models import Account, Category, Subcategory, User


class ReferenceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_user(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def get_account(self, account_id: int) -> Account | None:
        return self.session.get(Account, account_id)

    def get_category(self, category_id: int) -> Category | None:
        return self.session.get(Category, category_id)

    def get_subcategory(self, subcategory_id: int) -> Subcategory | None:
        return self.session.get(Subcategory, subcategory_id)

    def list_accounts(self, user_id: int, *, active_only: bool = False) -> list[Account]:
        statement = select(Account).where(Account.user_id == user_id).order_by(Account.name)
        if active_only:
            statement = statement.where(Account.is_active.is_(True))
        return list(self.session.scalars(statement))

    def list_categories(
        self,
        user_id: int,
        *,
        category_type: object | None = None,
        active_only: bool = False,
    ) -> list[Category]:
        statement = (
            select(Category)
            .where(Category.user_id == user_id)
            .options(selectinload(Category.subcategories))
            .order_by(Category.name)
        )
        if category_type is not None:
            statement = statement.where(Category.type == category_type)
        if active_only:
            statement = statement.where(Category.is_active.is_(True))
        return list(self.session.scalars(statement))

    def list_subcategories(
        self, category_id: int, *, active_only: bool = False
    ) -> list[Subcategory]:
        statement = (
            select(Subcategory)
            .where(Subcategory.category_id == category_id)
            .order_by(Subcategory.name)
        )
        if active_only:
            statement = statement.where(Subcategory.is_active.is_(True))
        return list(self.session.scalars(statement))
