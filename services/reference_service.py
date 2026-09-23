"""Mutações simples para usuário operacional, contas e categorias."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Account, AccountType, Category, CategoryType, Subcategory, User


class ReferenceServiceError(ValueError):
    """Erro de validação em cadastros de referência."""


class BootstrapService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create_operational_user(self) -> int:
        user_id = self.session.scalar(
            select(User.id).where(User.is_active.is_(True)).order_by(User.id).limit(1)
        )
        if user_id is not None:
            return user_id
        user = User(name="Usuário Aurora", email="usuario@aurora.local", currency="BRL")
        self.session.add(user)
        self.session.flush()
        return user.id


class AccountService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_account(
        self,
        *,
        user_id: int,
        name: str,
        account_type: AccountType,
        initial_balance: Decimal,
        initial_balance_date: date | None,
        institution: str | None = None,
    ) -> Account:
        clean_name = name.strip()
        if not clean_name:
            raise ReferenceServiceError("Informe o nome da conta.")
        self._validate_money(initial_balance)
        account = Account(
            user_id=user_id,
            name=clean_name,
            institution=institution.strip() if institution and institution.strip() else None,
            account_type=account_type,
            initial_balance=initial_balance,
            initial_balance_date=initial_balance_date,
            is_active=True,
        )
        self.session.add(account)
        try:
            self.session.flush()
        except IntegrityError as error:
            raise ReferenceServiceError("Já existe uma conta com esse nome.") from error
        return account

    @staticmethod
    def _validate_money(value: Decimal) -> None:
        if not isinstance(value, Decimal):
            raise TypeError("Valores monetários devem utilizar Decimal.")
        if not value.is_finite() or value.quantize(Decimal("0.01")) != value:
            raise ReferenceServiceError("Informe um valor monetário válido.")


class CategoryService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_category(
        self, *, user_id: int, name: str, category_type: CategoryType
    ) -> Category:
        clean_name = name.strip()
        if not clean_name:
            raise ReferenceServiceError("Informe o nome da categoria.")
        category = Category(
            user_id=user_id,
            name=clean_name,
            type=category_type,
            is_active=True,
        )
        self.session.add(category)
        try:
            self.session.flush()
        except IntegrityError as error:
            raise ReferenceServiceError("Essa categoria já está cadastrada.") from error
        return category

    def create_subcategory(
        self, *, user_id: int, category_id: int, name: str
    ) -> Subcategory:
        category = self.session.get(Category, category_id)
        if category is None or category.user_id != user_id or not category.is_active:
            raise ReferenceServiceError("A categoria selecionada não está disponível.")
        clean_name = name.strip()
        if not clean_name:
            raise ReferenceServiceError("Informe o nome da subcategoria.")
        subcategory = Subcategory(category_id=category_id, name=clean_name, is_active=True)
        self.session.add(subcategory)
        try:
            self.session.flush()
        except IntegrityError as error:
            raise ReferenceServiceError("Essa subcategoria já está cadastrada.") from error
        return subcategory
