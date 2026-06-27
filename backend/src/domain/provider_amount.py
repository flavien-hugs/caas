"""
Pure helper to extract the amount actually paid, across payment providers.

Kkiapay exposes ``amount`` at the top level of its verify response. CinetPay
nests it under ``raw_data.data.amount``. Returns ``None`` when the provider
does not report an amount in a format we can read — the caller treats
``None`` as "skip the amount equality guard" (best-effort) rather than as
"amount mismatch" (which would wrongly fail-close every CinetPay sync).

Ported from :py:func:`app.commands.synchronise._extract_provider_amount`.
"""

from __future__ import annotations

from typing import Any


def extract_provider_amount(verify_result: Any) -> float | None:
    if not isinstance(verify_result, dict):
        return None

    amount = verify_result.get("amount")
    if amount is None:
        raw = verify_result.get("raw_data")
        if isinstance(raw, dict):
            data = raw.get("data")
            if isinstance(data, dict):
                amount = data.get("amount")

    try:
        return float(amount) if amount is not None else None
    except (TypeError, ValueError):
        return None
