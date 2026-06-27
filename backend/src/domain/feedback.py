from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Feedback:
    """User review / star rating posted from a landing page."""

    id: str
    user_name: str
    rating: int  # 1..5
    message: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def new(cls, user_name: str, rating: int, message: str) -> "Feedback":
        if not (1 <= rating <= 5):
            raise ValueError(f"rating must be in 1..5, got {rating}")
        return cls(id=str(uuid.uuid4()), user_name=user_name, rating=rating, message=message)
