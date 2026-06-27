"""
Password hashing helpers — bcrypt with a sane default cost.

Lives in the domain layer because:
- it has no framework dep (just ``bcrypt``);
- the User aggregate carries a ``password_hash`` value, the domain has to
  know how to mint and verify them;
- swapping the algorithm later (argon2id, …) is a one-file change.
"""

from __future__ import annotations

import bcrypt

_DEFAULT_ROUNDS = 12  # ~250ms on a modern CPU, classic safe trade-off


def hash_password(plain: str, *, rounds: int = _DEFAULT_ROUNDS) -> str:
    """Return a bcrypt hash of ``plain`` as a UTF-8 string."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Timing-constant compare of a candidate against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (TypeError, ValueError):
        return False
