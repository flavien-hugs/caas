"""Config secret encryption: round-trip, idempotency, plaintext passthrough."""

from __future__ import annotations

from src.infrastructure.config.crypto import _PREFIX, decrypt, encrypt


def test_encrypt_decrypt_roundtrip():
    token = encrypt("super-secret")
    assert token != "super-secret"
    assert token.startswith(_PREFIX)
    assert decrypt(token) == "super-secret"


def test_encrypt_is_idempotent_on_already_encrypted():
    once = encrypt("value")
    twice = encrypt(once)
    assert once == twice
    assert decrypt(twice) == "value"


def test_empty_value_passes_through():
    assert encrypt("") == ""
    assert decrypt("") == ""


def test_decrypt_plaintext_passthrough():
    # Env-seeded / legacy values aren't prefixed — they must resolve as-is.
    assert decrypt("plain-env-secret") == "plain-env-secret"
