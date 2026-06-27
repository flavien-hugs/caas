from __future__ import annotations

from typing import Protocol

from src.domain.feedback import Feedback


class FeedbackRepositoryPort(Protocol):
    async def add(self, feedback: Feedback) -> None: ...

    async def list_recent_high_rated(self, min_rating: int = 4, limit: int = 10) -> list[Feedback]:
        """Used by the public landing page to display social proof."""
        ...
