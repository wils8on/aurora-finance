"""Enumerações dos modelos fundamentais."""

from enum import Enum


class AccountType(str, Enum):
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    CASH = "CASH"
    DIGITAL = "DIGITAL"
    OTHER = "OTHER"


class CategoryType(str, Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class TransactionType(str, Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class TransactionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"


class DerivedTransactionStatus(str, Enum):
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    SETTLED = "SETTLED"
    CANCELLED = "CANCELLED"
