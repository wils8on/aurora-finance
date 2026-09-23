"""Regras financeiras para Transaction e Settlement."""

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from models import (
    Category,
    CategoryType,
    DerivedTransactionStatus,
    Settlement,
    Subcategory,
    Transaction,
    TransactionStatus,
    TransactionType,
)
from repositories import ReferenceRepository, SettlementRepository, TransactionRepository


class TransactionServiceError(ValueError):
    """Erro de validação de uma operação financeira."""


class TransactionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.transactions = TransactionRepository(session)
        self.settlements = SettlementRepository(session)
        self.references = ReferenceRepository(session)

    def create_transaction(
        self,
        *,
        user_id: int,
        category_id: int,
        transaction_type: TransactionType,
        description: str,
        amount: Decimal,
        competence_date: date,
        subcategory_id: int | None = None,
        due_date: date | None = None,
        notes: str | None = None,
    ) -> Transaction:
        self._require_user(user_id)
        category = self._require_category(user_id, category_id, transaction_type)
        self._validate_subcategory(category, subcategory_id)
        self._validate_description(description)
        self._validate_money(amount)

        transaction = Transaction(
            user_id=user_id,
            category_id=category_id,
            subcategory_id=subcategory_id,
            transaction_type=transaction_type,
            status=TransactionStatus.ACTIVE,
            description=description.strip(),
            amount=amount,
            competence_date=competence_date,
            due_date=due_date,
            notes=notes,
        )
        self.transactions.add(transaction)
        self.session.flush()
        return transaction

    def create_settled_historical_transaction(
        self,
        *,
        user_id: int,
        category_id: int,
        account_id: int,
        transaction_type: TransactionType,
        description: str,
        amount: Decimal,
        competence_date: date,
        settled_at: datetime,
        subcategory_id: int | None = None,
        due_date: date | None = None,
        transaction_notes: str | None = None,
        settlement_notes: str | None = None,
    ) -> tuple[Transaction, Settlement]:
        self._require_account(user_id, account_id)

        with self.session.begin_nested():
            transaction = self.create_transaction(
                user_id=user_id,
                category_id=category_id,
                subcategory_id=subcategory_id,
                transaction_type=transaction_type,
                description=description,
                amount=amount,
                competence_date=competence_date,
                due_date=due_date,
                notes=transaction_notes,
            )
            settlement = self.add_settlement(
                transaction_id=transaction.id,
                user_id=user_id,
                account_id=account_id,
                amount=amount,
                settled_at=settled_at,
                notes=settlement_notes,
            )

        return transaction, settlement

    def add_settlement(
        self,
        *,
        transaction_id: int,
        user_id: int,
        account_id: int,
        amount: Decimal,
        settled_at: datetime,
        notes: str | None = None,
    ) -> Settlement:
        self._validate_money(amount)
        transaction = self._require_transaction_for_update(user_id, transaction_id)
        self._require_account(user_id, account_id)

        if transaction.status == TransactionStatus.CANCELLED:
            raise TransactionServiceError("Transaction cancelada não aceita Settlement.")

        settled_amount = self.settlements.total_for_transaction(transaction.id)
        if settled_amount + amount > transaction.amount:
            raise TransactionServiceError("Settlements não podem exceder o valor nominal.")

        settlement = Settlement(
            transaction_id=transaction.id,
            account_id=account_id,
            amount=amount,
            settled_at=settled_at,
            notes=notes,
        )
        self.settlements.add(settlement)
        self.session.flush()
        return settlement

    def cancel_transaction(
        self,
        *,
        transaction_id: int,
        user_id: int,
        cancellation_reason: str | None = None,
        cancelled_at: datetime | None = None,
    ) -> Transaction:
        transaction = self._require_transaction_for_update(user_id, transaction_id)
        if transaction.status == TransactionStatus.CANCELLED:
            raise TransactionServiceError("Transaction já está cancelada.")
        if self.settlements.total_for_transaction(transaction.id) > Decimal("0.00"):
            raise TransactionServiceError("Transaction com Settlement não pode ser cancelada.")

        transaction.status = TransactionStatus.CANCELLED
        transaction.cancelled_at = cancelled_at or datetime.now(timezone.utc)
        transaction.cancellation_reason = (
            cancellation_reason.strip() if cancellation_reason else None
        )
        self.session.flush()
        return transaction

    def get_settled_amount(self, transaction_id: int, user_id: int) -> Decimal:
        transaction = self._require_transaction(user_id, transaction_id)
        return self.settlements.total_for_transaction(transaction.id)

    def get_remaining_amount(self, transaction_id: int, user_id: int) -> Decimal:
        transaction = self._require_transaction(user_id, transaction_id)
        return transaction.amount - self.settlements.total_for_transaction(transaction.id)

    def get_derived_status(
        self, transaction_id: int, user_id: int
    ) -> DerivedTransactionStatus:
        transaction = self._require_transaction(user_id, transaction_id)
        if transaction.status == TransactionStatus.CANCELLED:
            return DerivedTransactionStatus.CANCELLED

        settled_amount = self.settlements.total_for_transaction(transaction.id)
        if settled_amount == Decimal("0.00"):
            return DerivedTransactionStatus.PENDING
        if settled_amount < transaction.amount:
            return DerivedTransactionStatus.PARTIAL
        return DerivedTransactionStatus.SETTLED

    def _require_user(self, user_id: int) -> None:
        if self.references.get_user(user_id) is None:
            raise TransactionServiceError("User não encontrado.")

    def _require_account(self, user_id: int, account_id: int) -> None:
        account = self.references.get_account(account_id)
        if account is None or account.user_id != user_id:
            raise TransactionServiceError("Account não pertence ao User informado.")

    def _require_category(
        self, user_id: int, category_id: int, transaction_type: TransactionType
    ) -> Category:
        category = self.references.get_category(category_id)
        if category is None or category.user_id != user_id:
            raise TransactionServiceError("Category não pertence ao User informado.")
        expected_type = CategoryType(transaction_type.value)
        if category.type != expected_type:
            raise TransactionServiceError("Category incompatível com TransactionType.")
        return category

    def _validate_subcategory(
        self, category: Category, subcategory_id: int | None
    ) -> Subcategory | None:
        if subcategory_id is None:
            return None
        subcategory = self.references.get_subcategory(subcategory_id)
        if subcategory is None or subcategory.category_id != category.id:
            raise TransactionServiceError("Subcategory não pertence à Category informada.")
        return subcategory

    def _require_transaction(self, user_id: int, transaction_id: int) -> Transaction:
        transaction = self.transactions.get(transaction_id)
        if transaction is None or transaction.user_id != user_id:
            raise TransactionServiceError("Transaction não pertence ao User informado.")
        return transaction

    def _require_transaction_for_update(
        self, user_id: int, transaction_id: int
    ) -> Transaction:
        transaction = self.transactions.get_for_update(transaction_id)
        if transaction is None or transaction.user_id != user_id:
            raise TransactionServiceError("Transaction não pertence ao User informado.")
        return transaction

    @staticmethod
    def _validate_description(description: str) -> None:
        if not description.strip():
            raise TransactionServiceError("Description é obrigatória.")

    @staticmethod
    def _validate_money(amount: Decimal) -> None:
        if not isinstance(amount, Decimal):
            raise TypeError("Valores monetários devem utilizar Decimal.")
        if not amount.is_finite() or amount <= Decimal("0.00"):
            raise TransactionServiceError("Valor monetário deve ser positivo.")
        if amount.quantize(Decimal("0.01")) != amount:
            raise TransactionServiceError("Valor monetário deve possuir no máximo 2 casas.")
