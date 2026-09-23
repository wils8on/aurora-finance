"""Consultas de leitura otimizadas para a interface Streamlit."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from zoneinfo import ZoneInfo

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from models import (
    Account,
    Category,
    CategoryType,
    DerivedTransactionStatus,
    Settlement,
    Subcategory,
    Transaction,
    TransactionStatus,
    TransactionType,
)

SAO_PAULO = ZoneInfo("America/Sao_Paulo")


class DatePerspective(str, Enum):
    COMPETENCE = "COMPETENCE"
    DUE = "DUE"
    CASH = "CASH"


@dataclass(frozen=True)
class TransactionFilters:
    user_id: int
    start_date: date
    end_date: date
    perspective: DatePerspective = DatePerspective.COMPETENCE
    transaction_type: TransactionType | None = None
    derived_status: DerivedTransactionStatus | None = None
    category_id: int | None = None
    subcategory_id: int | None = None
    search: str = ""
    include_cancelled: bool = False
    page: int = 1
    page_size: int = 25


@dataclass(frozen=True)
class TransactionListItem:
    id: int
    description: str
    transaction_type: TransactionType
    category_name: str
    subcategory_name: str | None
    competence_date: date
    due_date: date | None
    reference_date: date
    amount: Decimal
    settled_amount: Decimal
    remaining_amount: Decimal
    period_settled_amount: Decimal
    derived_status: DerivedTransactionStatus


@dataclass(frozen=True)
class SettlementHistoryItem:
    account_name: str
    amount: Decimal
    settled_at: datetime
    notes: str | None


@dataclass(frozen=True)
class TransactionDetail:
    id: int
    description: str
    transaction_type: TransactionType
    persisted_status: TransactionStatus
    derived_status: DerivedTransactionStatus
    category_name: str
    subcategory_name: str | None
    amount: Decimal
    settled_amount: Decimal
    remaining_amount: Decimal
    competence_date: date
    due_date: date | None
    cancelled_at: datetime | None
    cancellation_reason: str | None
    notes: str | None
    settlements: tuple[SettlementHistoryItem, ...]


@dataclass(frozen=True)
class TransactionSummary:
    primary_1: Decimal
    primary_2: Decimal
    primary_3: Decimal
    receivable: Decimal = Decimal("0.00")
    payable: Decimal = Decimal("0.00")


@dataclass(frozen=True)
class PaginatedTransactions:
    items: tuple[TransactionListItem, ...]
    total: int
    page: int
    page_size: int

    @property
    def pages(self) -> int:
        return max(1, (self.total + self.page_size - 1) // self.page_size)


@dataclass(frozen=True)
class AccountOption:
    id: int
    name: str
    institution: str | None
    account_type: str
    initial_balance: Decimal
    initial_balance_date: date | None
    is_active: bool


@dataclass(frozen=True)
class SubcategoryOption:
    id: int
    name: str
    is_active: bool


@dataclass(frozen=True)
class CategoryOption:
    id: int
    name: str
    category_type: CategoryType
    is_active: bool
    subcategories: tuple[SubcategoryOption, ...]


class TransactionQueryService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_transactions(self, filters: TransactionFilters) -> PaginatedTransactions:
        query, columns = self._filtered_query(filters)
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0

        today = date.today()
        if filters.perspective == DatePerspective.CASH:
            query = query.order_by(columns.reference_date.desc(), Transaction.id.desc())
        else:
            urgency = case(
                (
                    and_(
                        columns.state.in_(["PENDING", "PARTIAL"]),
                        Transaction.due_date < today,
                    ),
                    1,
                ),
                (
                    and_(
                        columns.state.in_(["PENDING", "PARTIAL"]),
                        Transaction.due_date == today,
                    ),
                    2,
                ),
                (
                    and_(
                        columns.state.in_(["PENDING", "PARTIAL"]),
                        Transaction.due_date > today,
                    ),
                    3,
                ),
                (
                    and_(
                        columns.state.in_(["PENDING", "PARTIAL"]),
                        Transaction.due_date.is_(None),
                    ),
                    4,
                ),
                (columns.state == "SETTLED", 5),
                else_=6,
            )
            query = query.order_by(
                urgency,
                Transaction.due_date.asc().nulls_last(),
                Transaction.competence_date.desc(),
                Transaction.id.desc(),
            )

        page = max(filters.page, 1)
        rows = self.session.execute(
            query.limit(filters.page_size).offset((page - 1) * filters.page_size)
        ).all()
        items = tuple(self._row_to_item(row, filters.perspective) for row in rows)
        return PaginatedTransactions(items, int(total), page, filters.page_size)

    def summarize(self, filters: TransactionFilters) -> TransactionSummary:
        query, _columns = self._filtered_query(filters)
        data = query.subquery()
        active = data.c.persisted_status == TransactionStatus.ACTIVE

        if filters.perspective == DatePerspective.CASH:
            received = self._sum(
                data,
                and_(data.c.transaction_type == TransactionType.INCOME, active),
                data.c.period_settled,
            )
            paid = self._sum(
                data,
                and_(data.c.transaction_type == TransactionType.EXPENSE, active),
                data.c.period_settled,
            )
            return TransactionSummary(received, paid, received - paid)

        receivable = self._sum(
            data,
            and_(data.c.transaction_type == TransactionType.INCOME, active),
            data.c.remaining,
        )
        payable = self._sum(
            data,
            and_(data.c.transaction_type == TransactionType.EXPENSE, active),
            data.c.remaining,
        )

        if filters.perspective == DatePerspective.DUE:
            overdue = self._sum(
                data,
                and_(active, data.c.due_date < date.today(), data.c.remaining > 0),
                data.c.remaining,
            )
            return TransactionSummary(receivable, payable, overdue)

        income = self._sum(
            data,
            and_(data.c.transaction_type == TransactionType.INCOME, active),
            data.c.nominal_amount,
        )
        expense = self._sum(
            data,
            and_(data.c.transaction_type == TransactionType.EXPENSE, active),
            data.c.nominal_amount,
        )
        return TransactionSummary(income, expense, income - expense, receivable, payable)

    def get_detail(self, transaction_id: int, user_id: int) -> TransactionDetail | None:
        statement = (
            select(Transaction)
            .where(Transaction.id == transaction_id, Transaction.user_id == user_id)
            .options(
                joinedload(Transaction.category),
                joinedload(Transaction.subcategory),
                selectinload(Transaction.settlements).joinedload(Settlement.account),
            )
        )
        transaction = self.session.scalar(statement)
        if transaction is None:
            return None
        settled = sum((item.amount for item in transaction.settlements), Decimal("0.00"))
        state = self._derive_status(transaction.status, settled, transaction.amount)
        history = tuple(
            SettlementHistoryItem(
                account_name=item.account.name,
                amount=item.amount,
                settled_at=item.settled_at,
                notes=item.notes,
            )
            for item in sorted(transaction.settlements, key=lambda item: item.settled_at, reverse=True)
        )
        return TransactionDetail(
            id=transaction.id,
            description=transaction.description,
            transaction_type=transaction.transaction_type,
            persisted_status=transaction.status,
            derived_status=state,
            category_name=transaction.category.name,
            subcategory_name=transaction.subcategory.name if transaction.subcategory else None,
            amount=transaction.amount,
            settled_amount=settled,
            remaining_amount=transaction.amount - settled,
            competence_date=transaction.competence_date,
            due_date=transaction.due_date,
            cancelled_at=transaction.cancelled_at,
            cancellation_reason=transaction.cancellation_reason,
            notes=transaction.notes,
            settlements=history,
        )

    def _filtered_query(self, filters: TransactionFilters):
        totals = (
            select(
                Settlement.transaction_id.label("transaction_id"),
                func.sum(Settlement.amount).label("settled_amount"),
            )
            .group_by(Settlement.transaction_id)
            .subquery()
        )
        start_dt = datetime.combine(filters.start_date, time.min, SAO_PAULO)
        end_dt = datetime.combine(filters.end_date + timedelta(days=1), time.min, SAO_PAULO)
        period = (
            select(
                Settlement.transaction_id.label("transaction_id"),
                func.sum(Settlement.amount).label("period_settled"),
                func.max(Settlement.settled_at).label("cash_reference"),
            )
            .where(Settlement.settled_at >= start_dt, Settlement.settled_at < end_dt)
            .group_by(Settlement.transaction_id)
            .subquery()
        )
        settled = func.coalesce(totals.c.settled_amount, Decimal("0.00"))
        period_settled = func.coalesce(period.c.period_settled, Decimal("0.00"))
        remaining = Transaction.amount - settled
        state = case(
            (Transaction.status == TransactionStatus.CANCELLED, "CANCELLED"),
            (settled == 0, "PENDING"),
            (settled < Transaction.amount, "PARTIAL"),
            else_="SETTLED",
        )
        reference_date = case(
            (filters.perspective == DatePerspective.COMPETENCE, Transaction.competence_date),
            (filters.perspective == DatePerspective.DUE, Transaction.due_date),
            else_=func.date(period.c.cash_reference),
        )
        query = (
            select(
                Transaction.id.label("id"),
                Transaction.description.label("description"),
                Transaction.transaction_type.label("transaction_type"),
                Transaction.status.label("persisted_status"),
                Transaction.amount.label("nominal_amount"),
                Transaction.competence_date.label("competence_date"),
                Transaction.due_date.label("due_date"),
                Category.name.label("category_name"),
                Subcategory.name.label("subcategory_name"),
                settled.label("settled_amount"),
                remaining.label("remaining"),
                period_settled.label("period_settled"),
                reference_date.label("reference_date"),
                state.label("derived_state"),
            )
            .join(Category, Category.id == Transaction.category_id)
            .outerjoin(Subcategory, Subcategory.id == Transaction.subcategory_id)
            .outerjoin(totals, totals.c.transaction_id == Transaction.id)
            .outerjoin(period, period.c.transaction_id == Transaction.id)
            .where(Transaction.user_id == filters.user_id)
        )

        if filters.perspective == DatePerspective.COMPETENCE:
            query = query.where(
                Transaction.competence_date.between(filters.start_date, filters.end_date)
            )
        elif filters.perspective == DatePerspective.DUE:
            query = query.where(Transaction.due_date.between(filters.start_date, filters.end_date))
        else:
            query = query.where(period_settled > 0)

        if not filters.include_cancelled and filters.derived_status is None:
            query = query.where(Transaction.status != TransactionStatus.CANCELLED)
        if filters.transaction_type:
            query = query.where(Transaction.transaction_type == filters.transaction_type)
        if filters.derived_status:
            query = query.where(state == filters.derived_status.value)
        if filters.category_id:
            query = query.where(Transaction.category_id == filters.category_id)
        if filters.subcategory_id:
            query = query.where(Transaction.subcategory_id == filters.subcategory_id)
        if filters.search.strip():
            term = f"%{filters.search.strip().lower()}%"
            query = query.where(
                or_(
                    func.lower(Transaction.description).like(term),
                    func.lower(Category.name).like(term),
                    func.lower(func.coalesce(Subcategory.name, "")).like(term),
                )
            )

        columns = type(
            "QueryColumns",
            (),
            {"state": state, "reference_date": reference_date},
        )
        return query, columns

    def _row_to_item(self, row, perspective: DatePerspective) -> TransactionListItem:
        reference = row.reference_date
        if isinstance(reference, str):
            reference = date.fromisoformat(reference)
        if reference is None:
            reference = row.due_date or row.competence_date
        return TransactionListItem(
            id=row.id,
            description=row.description,
            transaction_type=row.transaction_type,
            category_name=row.category_name,
            subcategory_name=row.subcategory_name,
            competence_date=row.competence_date,
            due_date=row.due_date,
            reference_date=reference,
            amount=Decimal(row.nominal_amount),
            settled_amount=Decimal(row.settled_amount),
            remaining_amount=Decimal(row.remaining),
            period_settled_amount=Decimal(row.period_settled),
            derived_status=DerivedTransactionStatus(row.derived_state),
        )

    def _sum(self, data, condition, column) -> Decimal:
        value = self.session.scalar(
            select(func.coalesce(func.sum(case((condition, column), else_=0)), 0)).select_from(data)
        )
        return Decimal(value)

    @staticmethod
    def _derive_status(
        status: TransactionStatus, settled: Decimal, amount: Decimal
    ) -> DerivedTransactionStatus:
        if status == TransactionStatus.CANCELLED:
            return DerivedTransactionStatus.CANCELLED
        if settled == Decimal("0.00"):
            return DerivedTransactionStatus.PENDING
        if settled < amount:
            return DerivedTransactionStatus.PARTIAL
        return DerivedTransactionStatus.SETTLED


class ReferenceQueryService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_accounts(self, user_id: int, *, active_only: bool = False) -> tuple[AccountOption, ...]:
        statement = select(Account).where(Account.user_id == user_id).order_by(Account.name)
        if active_only:
            statement = statement.where(Account.is_active.is_(True))
        return tuple(
            AccountOption(
                item.id,
                item.name,
                item.institution,
                item.account_type.value,
                item.initial_balance,
                item.initial_balance_date,
                item.is_active,
            )
            for item in self.session.scalars(statement)
        )

    def list_categories(
        self,
        user_id: int,
        *,
        category_type: CategoryType | None = None,
        active_only: bool = False,
    ) -> tuple[CategoryOption, ...]:
        statement = (
            select(Category)
            .where(Category.user_id == user_id)
            .options(selectinload(Category.subcategories))
            .order_by(Category.name)
        )
        if category_type:
            statement = statement.where(Category.type == category_type)
        if active_only:
            statement = statement.where(Category.is_active.is_(True))
        return tuple(
            CategoryOption(
                item.id,
                item.name,
                item.type,
                item.is_active,
                tuple(
                    SubcategoryOption(sub.id, sub.name, sub.is_active)
                    for sub in sorted(item.subcategories, key=lambda sub: sub.name)
                    if not active_only or sub.is_active
                ),
            )
            for item in self.session.scalars(statement)
        )
