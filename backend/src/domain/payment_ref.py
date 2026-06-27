from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique


@unique
class PaymentProviderName(str, Enum):
    KKIAPAY = "kkiapay"
    CINETPAY = "cinetpay"


@dataclass(frozen=True, slots=True)
class PaymentReference:
    """
    Stable handle to a payment on the provider side.

    For Kkiapay the ``provider_tx_id`` is the widget's ``transactionId``,
    persisted on the row only after the browser callback (or the beacon)
    fires. For CinetPay it is the internal ``Purchase.id`` used at
    initiation. Empty until the link is known.
    """

    provider: PaymentProviderName
    provider_tx_id: str | None = None
