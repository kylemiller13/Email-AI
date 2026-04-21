from fastapi import APIRouter, HTTPException
from api.models.schemas import MetricsResponse
from db.database import get_metrics, get_all_feedback
import subprocess
import os

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/metrics", response_model=MetricsResponse)
async def get_admin_metrics(user_email: str):
    """Get model performance metrics scoped to a user."""
    try:
        metrics = get_metrics(user_email)
        return MetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback")
async def get_all_feedback_entries(user_email: str):
    """Get feedback entries for a specific user."""
    try:
        feedback_rows = get_all_feedback(user_email)
        return [
            {
                "id": row["id"],
                "email_id": row["email_id"],
                "sender": row["sender"],
                "subject": row["subject"],
                "user_correction": row["user_correction"],
                "reported_at": row["reported_at"],
                "notes": row["notes"],
                "original_classification": row["classification"],
                "original_risk_level": row["risk_level"],
            }
            for row in feedback_rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrain")
async def retrain_model():
    """Trigger model retraining."""
    try:
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        python = "python3"
        result = subprocess.run(
            [python, "-m", "ml.train"],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=project_root,
        )

        if result.returncode != 0:
            raise Exception(result.stderr or result.stdout or "Training failed")

        return {
            "status": "success",
            "message": "Model retrained successfully",
            "output": result.stdout,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Training timed out after 5 minutes")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
