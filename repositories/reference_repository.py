"""Consultas simples das entidades referenciadas pelo núcleo financeiro."""

from sqlalchemy.orm import Session

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
