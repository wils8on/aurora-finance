"""Persistência e consultas de Transaction e Settlement."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from models import Settlement, Transaction


class TransactionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, transaction: Transaction) -> Transaction:
        self.session.add(transaction)
        return transaction

    def get(self, transaction_id: int) -> Transaction | None:
        return self.session.get(Transaction, transaction_id)

    def get_with_settlements(self, transaction_id: int) -> Transaction | None:
        statement = (
            select(Transaction)
            .where(Transaction.id == transaction_id)
            .options(selectinload(Transaction.settlements))
        )
        return self.session.scalar(statement)

    def get_for_update(self, transaction_id: int) -> Transaction | None:
        statement = select(Transaction).where(Transaction.id == transaction_id).with_for_update()
        return self.session.scalar(statement)


class SettlementRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, settlement: Settlement) -> Settlement:
        self.session.add(settlement)
        return settlement

    def total_for_transaction(self, transaction_id: int) -> Decimal:
        statement = select(func.coalesce(func.sum(Settlement.amount), 0)).where(
            Settlement.transaction_id == transaction_id
        )
        total = self.session.scalar(statement)
        return Decimal(total)
