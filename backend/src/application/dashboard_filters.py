"""
Shared filter DTO for the read-side dashboard queries.

Pure dataclass so it can be passed around between use cases (list, stats,
chart, export) and through to the persistence port without dragging in
HTTP or framework dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class TransactionFilters:
    q: str | None = None
    status: str | None = None
    book_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    # If True, drop the legacy ``amount >= min_price`` floor (used by the
    # dashboard toggle to surface low-amount or test transactions).
    include_low_amount: bool = False
    # Resolved min_price applied unless ``include_low_amount``. Kept on the
    # filter DTO so use cases don't need to know the settings.
    min_amount: int = 0
