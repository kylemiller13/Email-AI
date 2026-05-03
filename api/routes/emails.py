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
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

router = APIRouter(prefix="/emails", tags=["emails"])

MAX_FETCH = 50  # max emails to pull per fetch

# Maps each warning-sign label to a plain-language tactic category
WARNING_TO_TACTIC: dict[str, str] = {
    "Contains urgency language": "Urgency & Pressure",
    "Subject line contains urgency words": "Urgency & Pressure",
    "Contains threatening language about account suspension": "Urgency & Pressure",
    "Requests credentials or sensitive personal info": "Credential Harvesting",
    "URL contains credential/login keyword": "Credential Harvesting",
    "Contains an HTML form (credential harvesting)": "Credential Harvesting",
    "URL uses raw IP address instead of domain": "Malicious Links",
    "Contains shortened/obfuscated URL": "Malicious Links",
    "URL with suspicious top-level domain (.xyz, .tk, etc.)": "Malicious Links",
    "Uses insecure HTTP links (not HTTPS)": "Malicious Links",
    "Contains multiple URLs": "Malicious Links",
    "Uses generic greeting (Dear Customer, Dear User)": "Impersonation",
    "Sender display name doesn't match email domain": "Impersonation",
    "Sent from a free email provider (Gmail, Yahoo, etc.)": "Spoofed Sender",
    "Sender domain contains unusual numbers or hyphens": "Spoofed Sender",
    "Contains money/prize/lottery language": "Financial Scam",
    "Contains JavaScript": "Technical Attack",
    "Excessive use of capital letters": "Aggressive Formatting",
    "Excessive exclamation marks": "Aggressive Formatting",
    "Heavy use of HTML formatting": "Aggressive Formatting",
    "References a file attachment": "Malicious Attachment",
}

# keyword (in normalized domain) → (display name, real domain)
BRAND_KEYWORDS: dict[str, tuple] = {
    "paypal": ("PayPal", "paypal.com"),
    "paypa": ("PayPal", "paypal.com"),
    "amazon": ("Amazon", "amazon.com"),
    "google": ("Google", "google.com"),
    "microsoft": ("Microsoft", "microsoft.com"),
    "apple": ("Apple", "apple.com"),
    "netflix": ("Netflix", "netflix.com"),
    "facebook": ("Facebook", "facebook.com"),
    "instagram": ("Instagram", "instagram.com"),
    "linkedin": ("LinkedIn", "linkedin.com"),
    "dropbox": ("Dropbox", "dropbox.com"),
    "chase": ("Chase Bank", "chase.com"),
    "wellsfargo": ("Wells Fargo", "wellsfargo.com"),
    "citibank": ("Citibank", "citibank.com"),
    "ebay": ("eBay", "ebay.com"),
    "fedex": ("FedEx", "fedex.com"),
    "bankofamerica": ("Bank of America", "bankofamerica.com"),
}


def _parse_received_at(date_str: str):
    """Parse ISO or RFC 2822 email date to a timezone-aware datetime."""
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        pass
    try:
        dt = parsedate_to_datetime(date_str)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _sender_domain(sender: str) -> str:
    """Extract the domain portion from a sender string."""
    m = re.search(r"@([\w.\-]+)", sender)
    return m.group(1).lower() if m else ""


def _normalize_domain(domain: str) -> str:
    """Replace common homograph digits so 'amaz0n' matches 'amazon'."""
    subs = {"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "6": "g", "8": "b"}
    return "".join(subs.get(c, c) for c in domain.lower())


def _detect_impersonation(domain: str):
    """Return (domain, brand_name, real_domain) if domain spoofs a known brand, else None."""
    norm = _normalize_domain(domain)
    for keyword, (brand_name, real_domain) in BRAND_KEYWORDS.items():
        if keyword in norm:
            if domain == real_domain or domain.endswith("." + real_domain):
                return None  # it IS the real domain
            return (domain, brand_name, real_domain)
    return None


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
        from google.auth.exceptions import RefreshError
        from googleapiclient.errors import HttpError

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

    except (RefreshError, HttpError) as e:
        status = getattr(getattr(e, "resp", None), "status", None)
        if isinstance(e, RefreshError) or status == 401:
            raise HTTPException(status_code=401, detail="Gmail session expired. Please sign in again.")
        raise HTTPException(status_code=500, detail=str(e))
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


@router.get("/summary")
async def get_email_summary(user_email: str, days: int = 30):
    """Return a phishing activity summary for the given time window."""
    try:
        rows = get_all_emails_with_results(user_email)

        now = datetime.now(timezone.utc)
        today = now.date()
        period_start = now - timedelta(days=days)
        prev_start = period_start - timedelta(days=days)

        current_phishing = []
        previous_phishing = []
        for row in rows:
            if row["classification"] != "phishing":
                continue
            dt = _parse_received_at(row["received_at"])
            if dt is None:
                continue
            if dt >= period_start:
                current_phishing.append(row)
            elif dt >= prev_start:
                previous_phishing.append(row)

        total = len(current_phishing)
        prev_total = len(previous_phishing)

        if prev_total == 0 and total == 0:
            trend, pct = "same", None
        elif prev_total == 0:
            trend, pct = "new", None
        elif total > prev_total:
            trend = "up"
            pct = round((total - prev_total) / prev_total * 100)
        elif total < prev_total:
            trend = "down"
            pct = round((prev_total - total) / prev_total * 100)
        else:
            trend, pct = "same", 0

        # Daily breakdown — one entry per day, oldest first
        daily: dict[str, int] = {}
        for i in range(days):
            day = today - timedelta(days=days - 1 - i)
            daily[str(day)] = 0
        for row in current_phishing:
            dt = _parse_received_at(row["received_at"])
            if dt:
                ds = str(dt.date())
                if ds in daily:
                    daily[ds] += 1
        daily_breakdown = [{"date": d, "count": c} for d, c in daily.items()]

        # Top tactic — aggregate warning signs into categories
        tactic_counter: Counter = Counter()
        for row in current_phishing:
            try:
                signs = json.loads(row["warning_signs"]) if row["warning_signs"] else []
            except Exception:
                signs = []
            for sign in signs:
                tactic_counter[WARNING_TO_TACTIC.get(sign, "Other")] += 1
        top_tactic = None
        if tactic_counter:
            label, count = tactic_counter.most_common(1)[0]
            top_tactic = {"label": label, "count": count}

        # Impersonated brands — deduplicated
        seen: set = set()
        impersonated = []
        for row in current_phishing:
            domain = _sender_domain(row["sender"] or "")
            result = _detect_impersonation(domain)
            if result and result[1] not in seen:
                seen.add(result[1])
                impersonated.append({
                    "spoofed": result[0],
                    "brand": result[1],
                    "real_domain": result[2],
                })

        return {
            "days": days,
            "total_threats": total,
            "previous_total": prev_total,
            "percent_change": pct,
            "trend": trend,
            "daily_breakdown": daily_breakdown,
            "top_tactic": top_tactic,
            "impersonated_domains": impersonated,
        }

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
