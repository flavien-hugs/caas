"""Public feedback routes.

- ``POST /v2/feedbacks`` accepts a star + message from any visitor.
- ``GET  /v2/feedbacks/recent`` returns the high-rated reviews used as social
  proof on the public landings (consumed by SvelteKit at render time).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from src.application.use_cases import (
    ListRecentFeedbacks,
    SubmitFeedback,
    SubmitFeedbackInput,
)
from src.infrastructure.http.deps import (
    list_recent_feedbacks_use_case,
    submit_feedback_use_case,
)
from src.infrastructure.http.schemas import FeedbackRequest, FeedbackResponse

router = APIRouter(tags=["feedback"])


@router.post("/feedbacks", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    body: FeedbackRequest,
    use_case: SubmitFeedback = Depends(submit_feedback_use_case),
) -> FeedbackResponse:
    feedback = await use_case.execute(SubmitFeedbackInput(user_name=body.user_name, rating=body.rating, message=body.message))
    return FeedbackResponse(
        id=feedback.id,
        user_name=feedback.user_name,
        rating=feedback.rating,
        message=feedback.message,
        created_at=feedback.created_at.isoformat(),
    )


@router.get("/feedbacks/recent", response_model=list[FeedbackResponse])
async def list_recent_feedbacks(
    min_rating: int = Query(4, ge=1, le=5),
    limit: int = Query(10, ge=1, le=50),
    use_case: ListRecentFeedbacks = Depends(list_recent_feedbacks_use_case),
) -> list[FeedbackResponse]:
    feedbacks = await use_case.execute(min_rating=min_rating, limit=limit)
    return [
        FeedbackResponse(
            id=f.id,
            user_name=f.user_name,
            rating=f.rating,
            message=f.message,
            created_at=f.created_at.isoformat(),
        )
        for f in feedbacks
    ]
