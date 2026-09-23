"""Formatação pt-BR e fronteira segura para valores monetários."""

from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from zoneinfo import ZoneInfo

SAO_PAULO = ZoneInfo("America/Sao_Paulo")
CENT = Decimal("0.01")


def parse_decimal(value: str) -> Decimal:
    """Converte entrada textual pt-BR ou canônica sem usar float."""
    clean = value.strip().replace("R$", "").replace(" ", "")
    if not clean:
        raise ValueError("Informe um valor.")
    if "," in clean:
        clean = clean.replace(".", "").replace(",", ".")
    try:
        number = Decimal(clean)
    except InvalidOperation as error:
        raise ValueError("Informe um valor monetário válido.") from error
    if not number.is_finite():
        raise ValueError("Informe um valor monetário válido.")
    rounded = number.quantize(CENT, rounding=ROUND_HALF_UP)
    if rounded != number:
        raise ValueError("Use no máximo duas casas decimais.")
    return rounded


def format_currency(value: Decimal) -> str:
    quantized = value.quantize(CENT, rounding=ROUND_HALF_UP)
    raw = f"{quantized:,.2f}"
    return f"R$ {raw.replace(',', '_').replace('.', ',').replace('_', '.')}"


def format_date(value: date | None) -> str:
    return value.strftime("%d/%m/%Y") if value else "Sem vencimento"


def localize_datetime(day: date, clock: time) -> datetime:
    return datetime.combine(day, clock, tzinfo=SAO_PAULO)


def format_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=SAO_PAULO)
    else:
        value = value.astimezone(SAO_PAULO)
    return value.strftime("%d/%m/%Y %H:%M")
