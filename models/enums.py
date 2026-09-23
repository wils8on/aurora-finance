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
