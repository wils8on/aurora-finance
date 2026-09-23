"""Semântica textual compartilhada pelas páginas financeiras."""

from datetime import date
from decimal import Decimal

from models import DerivedTransactionStatus, TransactionType

STATUS_LABELS = {
    DerivedTransactionStatus.PENDING: "⏳ Pendente",
    DerivedTransactionStatus.PARTIAL: "◔ Parcial",
    DerivedTransactionStatus.SETTLED: "✓ Liquidada",
    DerivedTransactionStatus.CANCELLED: "— Cancelada",
}

TYPE_LABELS = {
    TransactionType.INCOME: "Receita",
    TransactionType.EXPENSE: "Despesa",
}


def due_condition(
    due_date: date | None,
    state: DerivedTransactionStatus,
    remaining_amount: Decimal,
    *,
    today: date | None = None,
) -> str:
    if state in (DerivedTransactionStatus.SETTLED, DerivedTransactionStatus.CANCELLED):
        return ""
    if due_date is None:
        return "Sem vencimento"
    reference = today or date.today()
    if due_date == reference:
        return "🗓 Vence hoje"
    if due_date < reference and remaining_amount > Decimal("0.00"):
        days = (reference - due_date).days
        return f"⚠ Vencida há {days} dia{'s' if days != 1 else ''}"
    return ""
