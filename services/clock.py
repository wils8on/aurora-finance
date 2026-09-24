"""Fonte temporal explícita da camada de aplicação."""

from datetime import date, datetime
from typing import Protocol
from zoneinfo import ZoneInfo

OPERATIONAL_TIMEZONE = ZoneInfo("America/Sao_Paulo")


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
