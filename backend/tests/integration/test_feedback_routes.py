"""Feedback flow end-to-end (POST /v2/feedbacks + GET /v2/feedbacks/recent)."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_submit_and_list_recent_feedback(client, db_session_factory):
    # Submit two feedbacks: one 5★ and one 2★. List should only return the 5★.
    r1 = await client.post(
        "/feedbacks",
        json={"user_name": "Alice", "rating": 5, "message": "Excellent !"},
    )
    assert r1.status_code == 201, r1.text
    assert r1.json()["rating"] == 5
    assert r1.json()["user_name"] == "Alice"

    r2 = await client.post(
        "/feedbacks",
        json={"user_name": "Bob", "rating": 2, "message": "Mitigé."},
    )
    assert r2.status_code == 201, r2.text

    r3 = await client.get("/feedbacks/recent?min_rating=4&limit=10")
    assert r3.status_code == 200
    items = r3.json()
    assert len(items) == 1
    assert items[0]["user_name"] == "Alice"


@pytest.mark.asyncio
async def test_submit_feedback_validates_rating_bounds(client):
    r = await client.post(
        "/feedbacks",
        json={"user_name": "X", "rating": 6, "message": "out of range"},
    )
    assert r.status_code == 422  # Pydantic Field(ge=1, le=5)
