"""
Module-level slowapi limiter singleton.

slowapi wants the decorator (``@limiter.limit(...)``) to reference the same
instance that the app's exception handler is bound to. Keeping the limiter
here lets the route module import it without circular deps, and lets the
test suite reach it to reset state between tests.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def reset_limiter() -> None:
    """Clear the in-memory limit storage. Test-only helper."""
    storage = getattr(limiter, "_storage", None)
    if storage is not None and hasattr(storage, "reset"):
        storage.reset()
