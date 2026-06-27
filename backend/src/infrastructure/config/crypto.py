"""
Symmetric encryption for config secrets stored in the DB.

Secrets (SMTP password, payment private keys, SMS API key) are encrypted at
rest with Fernet (AES-128-CBC + HMAC). The key comes from
``CONFIG_ENCRYPTION_KEY``; when unset it is derived from ``SESSION_SECRET`` so
existing single-secret deployments keep working, with a startup warning. In
``production`` an explicit key is required — a derived key tied to the session
secret would rotate the session out and lock every stored secret.
"""

from __future__ import annotations

import base64
import hashlib
import logging
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from src.infrastructure.config.settings import settings

log = logging.getLogger(__name__)

_PREFIX = "enc::"  # marks an already-encrypted value (idempotent encrypt)


def _derive_key(material: str) -> bytes:
    """A urlsafe-base64 32-byte Fernet key from arbitrary secret material."""
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    # Cached so the ephemeral-key dev fallback stays stable within a process
    # (otherwise a fresh key per call would make encrypt/decrypt round-trips
    # fail). Production/staging set an explicit key, so caching is a no-op there.
    if settings.CONFIG_ENCRYPTION_KEY:
        key = settings.CONFIG_ENCRYPTION_KEY.encode("utf-8")
        # Accept both a raw 32-byte urlsafe key and arbitrary material.
        try:
            return Fernet(key)
        except (ValueError, TypeError):
            return Fernet(_derive_key(settings.CONFIG_ENCRYPTION_KEY))

    if settings.ENVIRONMENT == "production":
        raise RuntimeError("CONFIG_ENCRYPTION_KEY is required in production to encrypt config secrets.")

    if settings.SESSION_SECRET:
        log.warning("CONFIG_ENCRYPTION_KEY unset — deriving config encryption key from SESSION_SECRET.")
        return Fernet(_derive_key(settings.SESSION_SECRET))

    log.warning("Neither CONFIG_ENCRYPTION_KEY nor SESSION_SECRET set — using an ephemeral key (dev only).")
    return Fernet(Fernet.generate_key())


def encrypt(plaintext: str) -> str:
    """Encrypt a secret. Idempotent: an already-encrypted value is returned as-is."""
    if not plaintext or plaintext.startswith(_PREFIX):
        return plaintext
    token = _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")
    return f"{_PREFIX}{token}"


def decrypt(value: str) -> str:
    """Decrypt a value produced by :func:`encrypt`. Plain (unprefixed) values
    pass through unchanged so env-seeded or legacy rows still resolve."""
    if not value or not value.startswith(_PREFIX):
        return value
    token = value[len(_PREFIX) :]
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        log.error("Failed to decrypt a config secret — wrong CONFIG_ENCRYPTION_KEY? Returning empty.")
        return ""
