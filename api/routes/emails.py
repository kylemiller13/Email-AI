from fastapi import APIRouter, HTTPException
from typing import List
from api.models.schemas import EmailScanRequest, EmailAnalysisResponse
from db.database import (
    insert_email,
    insert_analysis_result,
    update_analysis_result,
    get_all_emails_with_results,
    get_email_with_result,
)
from ml.predict import predict
import json

router = APIRouter(prefix="/emails", tags=["emails"])


@router.post("/scan", response_model=EmailAnalysisResponse)
async def scan_email(request: EmailScanRequest):
    """Scan an email for phishing indicators."""
    try:
        # Insert email into database
        email_id = insert_email(
            gmail_id=request.gmail_id,
            sender=request.sender,
            subject=request.subject,
            body=request.body,
            received_at=request.received_at,
            user_email=request.user_email,
        )
        
        # Run prediction with full email context
        analysis = predict(body=request.body, subject=request.subject, sender=request.sender)
        
        # Save analysis result
        warning_signs_json = json.dumps(analysis["warning_signs"])
        insert_analysis_result(
            email_id=email_id,
            classification=analysis["classification"],
            confidence_score=analysis["confidence_score"],
            risk_level=analysis["risk_level"],
            warning_signs=warning_signs_json,
            explanation=analysis["explanation"],
        )
        
        # Return full response
        return EmailAnalysisResponse(
            email_id=email_id,
            gmail_id=request.gmail_id,
            sender=request.sender,
            subject=request.subject,
            body=request.body,
            received_at=request.received_at,
            user_email=request.user_email,
            classification=analysis["classification"],
            confidence_score=analysis["confidence_score"],
            risk_level=analysis["risk_level"],
            warning_signs=analysis["warning_signs"],
            explanation=analysis["explanation"],
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[EmailAnalysisResponse])
async def get_emails(user_email: str):
    """Get all analyzed emails for a user."""
    try:
        rows = get_all_emails_with_results(user_email)
        results = []
        for row in rows:
            warning_signs = json.loads(row["warning_signs"]) if row["warning_signs"] else []
            results.append(
                EmailAnalysisResponse(
                    email_id=row["id"],
                    gmail_id=row["gmail_id"],
                    sender=row["sender"],
                    subject=row["subject"],
                    body=row["body"],
                    received_at=row["received_at"],
                    user_email=row["user_email"],
                    classification=row["classification"] or "unknown",
                    confidence_score=row["confidence_score"] or 0.0,
                    risk_level=row["risk_level"] or "unknown",
                    warning_signs=warning_signs,
                    explanation=row["explanation"] or "Not analyzed",
                    analyzed_at=row["analyzed_at"],
                )
            )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rescan")
async def rescan_all_emails(user_email: str):
    """Re-run prediction on all stored emails and update analysis results."""
    try:
        from db.database import get_db
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.id, e.sender, e.subject, e.body
                FROM emails e
                JOIN analysis_results ar ON e.id = ar.email_id
                WHERE e.user_email = ?
                """,
                (user_email,),
            )
            rows = cursor.fetchall()

        updated = 0
        for row in rows:
            analysis = predict(body=row["body"], subject=row["subject"], sender=row["sender"])
            update_analysis_result(
                email_id=row["id"],
                classification=analysis["classification"],
                confidence_score=analysis["confidence_score"],
                risk_level=analysis["risk_level"],
                warning_signs=json.dumps(analysis["warning_signs"]),
                explanation=analysis["explanation"],
            )
            updated += 1

        return {"updated": updated, "message": f"Re-scanned {updated} email(s) successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{email_id}", response_model=EmailAnalysisResponse)
async def get_email(email_id: int):
    """Get a specific email with its analysis result."""
    try:
        row = get_email_with_result(email_id)
        if not row:
            raise HTTPException(status_code=404, detail="Email not found")
        
        warning_signs = json.loads(row["warning_signs"]) if row["warning_signs"] else []
        return EmailAnalysisResponse(
            email_id=row["id"],
            gmail_id=row["gmail_id"],
            sender=row["sender"],
            subject=row["subject"],
            body=row["body"],
            received_at=row["received_at"],
            user_email=row["user_email"],
            classification=row["classification"] or "unknown",
            confidence_score=row["confidence_score"] or 0.0,
            risk_level=row["risk_level"] or "unknown",
            warning_signs=warning_signs,
            explanation=row["explanation"] or "Not analyzed",
            analyzed_at=row["analyzed_at"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
