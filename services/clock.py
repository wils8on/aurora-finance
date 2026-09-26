"""Fonte temporal explícita da camada de aplicação."""

from datetime import date, datetime, time, timedelta, timezone
from typing import Protocol
from zoneinfo import ZoneInfo

OPERATIONAL_TIMEZONE = ZoneInfo("America/Sao_Paulo")


def operational_date(value: datetime) -> date:
    """Retorna o dia financeiro de um instante persistido em UTC.

    SQLite perde o offset de ``DateTime(timezone=True)``; por contrato esses
    valores ingênuos representam UTC. PostgreSQL preserva o instante com
    timezone, portanto ambos os casos convergem antes da conversão operacional.
    """
    if value.tzinfo is None or value.utcoffset() is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(OPERATIONAL_TIMEZONE).date()


def operational_period_utc(start: date, end: date) -> tuple[datetime, datetime]:
    """Converte um intervalo inclusivo de dias operacionais em limites UTC."""
    start_at = datetime.combine(start, time.min, OPERATIONAL_TIMEZONE)
    end_at = datetime.combine(end + timedelta(days=1), time.min, OPERATIONAL_TIMEZONE)
    return start_at.astimezone(timezone.utc), end_at.astimezone(timezone.utc)


class Clock(Protocol):
    """Contrato mínimo para decisões dependentes do tempo."""

    def today(self) -> date:
        ...

    def now(self) -> datetime:
        ...


class SystemClock:
    """Relógio padrão no timezone operacional do Aurora Finance."""

    def today(self) -> date:
        return self.now().date()

    def now(self) -> datetime:
        return datetime.now(OPERATIONAL_TIMEZONE)


class FixedClock:
    """Relógio determinístico para testes e casos de uso controlados."""

    def __init__(self, current: datetime) -> None:
        if current.tzinfo is None or current.utcoffset() is None:
            raise ValueError("FixedClock exige datetime timezone-aware.")
        self._current = current.astimezone(OPERATIONAL_TIMEZONE)

    def today(self) -> date:
        return self._current.date()

    def now(self) -> datetime:
        return self._current
