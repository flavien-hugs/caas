"""Feedback use cases (submit + list recent)."""

from __future__ import annotations

from dataclasses import dataclass

from src.application.ports import FeedbackRepositoryPort
from src.domain import Feedback


@dataclass(frozen=True, slots=True)
class SubmitFeedbackInput:
    user_name: str
    rating: int
    message: str


class SubmitFeedback:
    def __init__(self, feedbacks: FeedbackRepositoryPort) -> None:
        self._feedbacks = feedbacks

    async def execute(self, cmd: SubmitFeedbackInput) -> Feedback:
        # Domain enforces rating 1..5; HTTP DTO bounds the strings.
        feedback = Feedback.new(user_name=cmd.user_name, rating=cmd.rating, message=cmd.message)
        await self._feedbacks.add(feedback)
        return feedback


class ListRecentFeedbacks:
    def __init__(self, feedbacks: FeedbackRepositoryPort) -> None:
        self._feedbacks = feedbacks

    async def execute(self, min_rating: int = 4, limit: int = 10) -> list[Feedback]:
        return await self._feedbacks.list_recent_high_rated(min_rating=min_rating, limit=limit)
