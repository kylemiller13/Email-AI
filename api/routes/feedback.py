from fastapi import APIRouter, HTTPException
from api.models.schemas import FeedbackRequest
from db.database import insert_feedback, get_feedback_for_email

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("")
async def submit_feedback(request: FeedbackRequest):
    """Submit user feedback on an email analysis."""
    try:
        feedback_id = insert_feedback(
            email_id=request.email_id,
            user_correction="flagged",
            notes=request.notes,
        )
        return {
            "feedback_id": feedback_id,
            "email_id": request.email_id,
            "message": "Email flagged for admin review.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{email_id}")
async def get_feedback(email_id: int):
    """Get all feedback for an email."""
    try:
        feedback_rows = get_feedback_for_email(email_id)
        return [
            {
                "id": row["id"],
                "email_id": row["email_id"],
                "user_correction": row["user_correction"],
                "reported_at": row["reported_at"],
                "notes": row["notes"],
            }
            for row in feedback_rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
