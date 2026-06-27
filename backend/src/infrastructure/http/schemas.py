"""
HTTP-layer DTOs. Sanitization of free-form strings happens here at the
boundary, never in the use case (which trusts its inputs).
"""

from __future__ import annotations

from typing import Annotated, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


def _sanitize(value: str, max_length: int) -> str:
    """
    Strip ASCII control characters and bound length.

    Defense-in-depth complement to the client-side escaping in the admin
    dashboard (see ``app/templates/pages/dashboard.html`` for the legacy
    sink). Mirrors :py:func:`app.routers.payment._sanitize`.
    """
    cleaned = "".join(c for c in value if c == " " or (c.isprintable() and c != "\x7f"))
    return cleaned.strip()[:max_length]


class PurchaseRequest(BaseModel):
    book_id: str = Field(min_length=1, max_length=60)
    email: EmailStr
    name: Annotated[str, Field(min_length=1, max_length=100)]
    surname: Annotated[str, Field(min_length=1, max_length=100)]
    phone: Annotated[str, Field(min_length=1, max_length=40)]
    country: Annotated[str, Field(min_length=1, max_length=80)]
    city: Annotated[str, Field(min_length=1, max_length=100)]
    latitude: float | None = None
    longitude: float | None = None
    client_amount: int | None = None
    offer: Optional[str] = Field(default=None, max_length=60)
    situation: Optional[str] = Field(default=None, max_length=60)

    @field_validator("name", "surname", "phone", "country", "city")
    @classmethod
    def _trim_short(cls, v: str) -> str:
        return _sanitize(v, 100)

    @field_validator("offer", "situation")
    @classmethod
    def _trim_optional(cls, v: str | None) -> str | None:
        return _sanitize(v, 60) if v else v


class PurchaseResponse(BaseModel):
    purchase_id: str
    payment_url: str
    amount: int
    currency: str


class PurchaseLookupResponse(BaseModel):
    """
    Public projection of a purchase used by SvelteKit's success/error
    pages to decide whether to render or redirect home.
    """

    id: str
    book_id: str
    status: str
    amount: int
    currency: str


class BeaconRequest(BaseModel):
    internal_tx_id: str = Field(min_length=1, max_length=64)
    transaction_id: str = Field(min_length=1, max_length=128)


class CallbackResponse(BaseModel):
    purchase_id: str
    status: str
    confirmed: bool
    delivered: bool


class FeedbackRequest(BaseModel):
    user_name: Annotated[str, Field(min_length=1, max_length=100)]
    rating: int = Field(ge=1, le=5)
    message: Annotated[str, Field(min_length=1, max_length=2000)]

    @field_validator("user_name", "message")
    @classmethod
    def _sanitize(cls, v: str) -> str:
        # Reuse the same control-char strip the purchase form does. Keeps
        # the admin dashboard rendering safe end-to-end.
        return _sanitize(v, 2000)


class FeedbackResponse(BaseModel):
    id: str
    user_name: str
    rating: int
    message: str
    created_at: str  # ISO 8601


# --- Admin dashboard ---------------------------------------------------------


class TransactionItem(BaseModel):
    id: str
    book_id: str
    user_email: str
    user_name: str
    user_phone: str
    user_country: str
    user_city: str
    amount: int
    currency: str
    status: str
    transaction_id: str | None
    created_at: str  # ISO 8601


class PaginatedTransactions(BaseModel):
    items: list[TransactionItem]
    total: int
    page: int
    size: int
    pages: int


class DashboardStatsResponse(BaseModel):
    total_revenue: float
    successful_sales: int
    pending_transactions: int
    failed_transactions: int
    total_transactions: int


class RevenuePointResponse(BaseModel):
    day: str  # YYYY-MM-DD
    revenue: float


class RevenueChartResponse(BaseModel):
    days: int
    series: list[RevenuePointResponse]
