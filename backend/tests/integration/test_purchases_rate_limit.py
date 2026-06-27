"""
Rate limit on POST /purchases — mirrors the legacy ``app/routers/payment.py``
``@limiter.limit("3/minute")`` policy.
"""

from __future__ import annotations

import pytest

PAYLOAD = {
    "book_id": "lutte-contre-fraude",
    "email": "c@example.com",
    "name": "Candidate",
    "surname": "Test",
    "phone": "+225 07 00 00 00 00",
    "country": "Côte d'Ivoire",
    "city": "Abidjan",
}


@pytest.mark.asyncio
async def test_fourth_purchase_within_a_minute_is_rate_limited(client, db_session_factory):
    """Three successful POSTs in a row, the fourth must come back 429."""
    for _ in range(3):
        r = await client.post("/purchases", json=PAYLOAD)
        assert r.status_code == 201, r.text

    r = await client.post("/purchases", json=PAYLOAD)
    assert r.status_code == 429, r.text
    # slowapi exposes the policy in the response body via its default handler
    assert "Rate limit exceeded" in r.text or "3" in r.text
