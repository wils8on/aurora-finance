"""Formatação visual pt-BR usada pelo protótipo Streamlit."""

from datetime import date, datetime, time
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from utils.money import CENT, parse_decimal

SAO_PAULO = ZoneInfo("America/Sao_Paulo")


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
