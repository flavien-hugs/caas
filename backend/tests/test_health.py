import pytest

from src.domain import (
    Currency,
    Customer,
    Money,
    PaymentProviderName,
    PaymentReference,
    Purchase,
    PurchaseStatus,
)


@pytest.mark.asyncio
async def test_health_endpoint(client):
    r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_domain_money_equality_within_tolerance():
    """Smoke check that the domain layer imports cleanly without framework deps."""
    a = Money(amount=10_000, currency=Currency.XOF)
    b = Money(amount=10_001, currency=Currency.XOF)
    c = Money(amount=10_005, currency=Currency.XOF)
    assert a.equals_within(b, tolerance=1)
    assert not a.equals_within(c, tolerance=1)


def test_domain_purchase_immutable_transitions():
    p = Purchase.new(
        book_id="lutte-contre-fraude",
        customer=Customer(email="x@y.z", name="X Y", phone="+225...", country="CI", city="Abidjan"),
        amount=Money(amount=20_000, currency=Currency.XOF),
        payment_ref=PaymentReference(provider=PaymentProviderName.KKIAPAY),
    )
    assert p.status is PurchaseStatus.PENDING
    p2 = p.with_status(PurchaseStatus.SUCCESS)
    assert p2.status is PurchaseStatus.SUCCESS
    assert p.status is PurchaseStatus.PENDING  # original untouched
