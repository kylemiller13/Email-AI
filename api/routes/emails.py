from fastapi import APIRouter, HTTPException, Request
from typing import List
from api.models.schemas import EmailScanRequest, EmailAnalysisResponse
from db.database import (
    insert_email,
    insert_analysis_result,
    update_analysis_result,
    get_all_emails_with_results,
    get_email_with_result,
    get_email_by_gmail_id,
)
from ml.predict import predict
import json
import base64

router = APIRouter(prefix="/emails", tags=["emails"])

MAX_FETCH = 50  # max emails to pull per fetch


def _decode_body(data: str) -> str:
    """Base64url-decode a Gmail message body part."""
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")


def _extract_plain_text(payload: dict) -> str:
    """Recursively pull plain-text body from a Gmail message payload."""
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if mime_type == "text/plain" and body_data:
        return _decode_body(body_data)

    if mime_type == "text/html" and body_data:
        # Fall back to HTML only if no plain part found higher up
        return _decode_body(body_data)

    for part in payload.get("parts", []):
        result = _extract_plain_text(part)
        if result:
            return result

    return ""


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


@router.post("/fetch-from-gmail")
async def fetch_from_gmail(request: Request, user_email: str):
    """Fetch recent emails from Gmail, analyze them, and store results."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth_header.removeprefix("Bearer ").strip()

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials(token=token)
        gmail = build("gmail", "v1", credentials=creds)

        list_resp = gmail.users().messages().list(
            userId="me", maxResults=MAX_FETCH
        ).execute()
        message_refs = list_resp.get("messages", [])

        fetched = 0
        skipped = 0

        for ref in message_refs:
            gmail_id = ref["id"]

            # Skip emails already in the database
            if get_email_by_gmail_id(gmail_id):
                skipped += 1
                continue

            msg = gmail.users().messages().get(
                userId="me", id=gmail_id, format="full"
            ).execute()

            payload = msg.get("payload", {})
            headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}

            subject = headers.get("subject", "(no subject)")
            sender = headers.get("from", "")
            date_str = headers.get("date", "")
            body = _extract_plain_text(payload)

            email_id = insert_email(
                gmail_id=gmail_id,
                sender=sender,
                subject=subject,
                body=body,
                received_at=date_str,
                user_email=user_email,
            )

            analysis = predict(body=body, subject=subject, sender=sender)
            insert_analysis_result(
                email_id=email_id,
                classification=analysis["classification"],
                confidence_score=analysis["confidence_score"],
                risk_level=analysis["risk_level"],
                warning_signs=json.dumps(analysis["warning_signs"]),
                explanation=analysis["explanation"],
            )
            fetched += 1

        return {
            "fetched": fetched,
            "skipped": skipped,
            "message": f"Fetched and analyzed {fetched} new email(s). {skipped} already in database.",
        }

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
