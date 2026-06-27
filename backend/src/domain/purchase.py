from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum, unique
from typing import Any

from .money import Money
from .payment_ref import PaymentReference


@unique
class PurchaseStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class Customer:
    email: str
    name: str
    phone: str
    country: str
    city: str
    ip: str | None = None
    user_agent: str | None = None
    latitude: float | None = None
    longitude: float | None = None


@dataclass(frozen=True, slots=True)
class Purchase:
    """
    Aggregate root for the checkout flow.

    Designed as an immutable record; state transitions return a new instance
    via :py:meth:`with_status` / :py:meth:`with_payment_ref` so the domain
    stays pure-functional and trivially testable.
    """

    id: str
    book_id: str
    customer: Customer
    amount: Money
    status: PurchaseStatus
    payment_ref: PaymentReference
    client_metadata: dict[str, Any] = field(default_factory=dict)
    payment_metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def new(
        cls,
        book_id: str,
        customer: Customer,
        amount: Money,
        payment_ref: PaymentReference,
        client_metadata: dict[str, Any] | None = None,
    ) -> "Purchase":
        return cls(
            id=str(uuid.uuid4()),
            book_id=book_id,
            customer=customer,
            amount=amount,
            status=PurchaseStatus.PENDING,
            payment_ref=payment_ref,
            client_metadata=client_metadata or {},
        )

    def with_status(self, status: PurchaseStatus) -> "Purchase":
        return replace(self, status=status, updated_at=datetime.utcnow())

    def with_payment_ref(self, ref: PaymentReference) -> "Purchase":
        return replace(self, payment_ref=ref, updated_at=datetime.utcnow())

    def merge_payment_metadata(self, **patch: Any) -> "Purchase":
        new_meta = {**self.payment_metadata, **patch}
        return replace(self, payment_metadata=new_meta, updated_at=datetime.utcnow())

    @property
    def has_security_error(self) -> bool:
        """
        True when a previous step flagged this purchase as security-failed
        (e.g. callback detected an amount mismatch). Such purchases must not
        be resurrected by sync / re-verification.
        """
        return bool(self.payment_metadata.get("security_error"))
