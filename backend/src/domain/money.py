"""Money value object.

Amounts are stored as integers in the smallest unit of the currency (e.g. for
XOF, the unit is 1 FCFA — there are no sub-units in mobile money flows). This
gets us out of float arithmetic for the amount-equality comparisons that
matter at the security boundary (callback amount-mismatch detection).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique


@unique
class Currency(str, Enum):
    XOF = "XOF"
    XAF = "XAF"
    EUR = "EUR"
    USD = "USD"


@dataclass(frozen=True, slots=True)
class Money:
    amount: int
    currency: Currency

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError(f"Money.amount must be non-negative, got {self.amount}")

    @classmethod
    def of(cls, amount: int | float, currency: Currency | str) -> Money:
        """
        Convenience constructor that accepts the historical float amounts
        used by the legacy schema and rounds them to the nearest unit.
        """
        cur = Currency(currency) if isinstance(currency, str) else currency
        return cls(amount=int(round(float(amount))), currency=cur)

    def equals_within(self, other: Money, tolerance: int = 1) -> bool:
        """
        Equality with a tolerance window (matches the 1 XOF callback rule).
        """
        if self.currency != other.currency:
            return False
        return abs(self.amount - other.amount) <= tolerance

    def __str__(self) -> str:
        return f"{self.amount} {self.currency.value}"
