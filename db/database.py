import sqlite3
import os
from contextlib import contextmanager
from typing import Optional

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "emails.db")


def get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize the database with schema."""
    conn = get_connection()
    cursor = conn.cursor()
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        schema = f.read()
    cursor.executescript(schema)
    conn.commit()
    conn.close()


def get_email_by_gmail_id(gmail_id: str) -> Optional[int]:
    """Get email id by gmail_id, returns None if not found."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM emails WHERE gmail_id = ?", (gmail_id,))
        result = cursor.fetchone()
        return result["id"] if result else None


def insert_email(
    gmail_id: str,
    sender: str,
    subject: str,
    body: str,
    received_at: str,
    user_email: str,
) -> int:
    """Insert an email into the database. If it already exists, return existing email id."""
    # Check if email already exists
    existing_id = get_email_by_gmail_id(gmail_id)
    if existing_id:
        return existing_id
    
    # Insert new email
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO emails (gmail_id, sender, subject, body, received_at, user_email)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (gmail_id, sender, subject, body, received_at, user_email),
        )
        return cursor.lastrowid


def insert_analysis_result(
    email_id: int,
    classification: str,
    confidence_score: float,
    risk_level: str,
    warning_signs: str,
    explanation: str,
) -> int:
    """Insert an analysis result into the database. If it already exists, return existing id."""
    # Check if analysis already exists for this email
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM analysis_results WHERE email_id = ?", (email_id,))
        existing = cursor.fetchone()
        if existing:
            return existing["id"]
    
    # Insert new analysis result
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO analysis_results
            (email_id, classification, confidence_score, risk_level, warning_signs, explanation)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (email_id, classification, confidence_score, risk_level, warning_signs, explanation),
        )
        return cursor.lastrowid


def update_analysis_result(
    email_id: int,
    classification: str,
    confidence_score: float,
    risk_level: str,
    warning_signs: str,
    explanation: str,
) -> None:
    """Update an existing analysis result for an email."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE analysis_results
            SET classification = ?, confidence_score = ?, risk_level = ?,
                warning_signs = ?, explanation = ?, analyzed_at = CURRENT_TIMESTAMP
            WHERE email_id = ?
            """,
            (classification, confidence_score, risk_level, warning_signs, explanation, email_id),
        )


def insert_feedback(
    email_id: int, user_correction: str, notes: Optional[str] = None
) -> int:
    """Insert user feedback into the database."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO feedback (email_id, user_correction, notes)
            VALUES (?, ?, ?)
            """,
            (email_id, user_correction, notes),
        )
        return cursor.lastrowid


def get_all_emails_with_results(user_email: str):
    """Get all emails for a user with their analysis results."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                e.id,
                e.gmail_id,
                e.sender,
                e.subject,
                e.body,
                e.received_at,
                e.user_email,
                ar.classification,
                ar.confidence_score,
                ar.risk_level,
                ar.warning_signs,
                ar.explanation,
                ar.analyzed_at
            FROM emails e
            LEFT JOIN analysis_results ar ON e.id = ar.email_id
            WHERE e.user_email = ?
            ORDER BY e.received_at DESC
            """,
            (user_email,),
        )
        return cursor.fetchall()


def get_email_with_result(email_id: int):
    """Get a specific email with its analysis result."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                e.id,
                e.gmail_id,
                e.sender,
                e.subject,
                e.body,
                e.received_at,
                e.user_email,
                ar.classification,
                ar.confidence_score,
                ar.risk_level,
                ar.warning_signs,
                ar.explanation,
                ar.analyzed_at
            FROM emails e
            LEFT JOIN analysis_results ar ON e.id = ar.email_id
            WHERE e.id = ?
            """,
            (email_id,),
        )
        return cursor.fetchone()


def get_feedback_for_email(email_id: int):
    """Get feedback for a specific email."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, email_id, user_correction, reported_at, notes
            FROM feedback
            WHERE email_id = ?
            ORDER BY reported_at DESC
            """,
            (email_id,),
        )
        return cursor.fetchall()


def get_all_feedback(user_email: str):
    """Get all feedback for a specific user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                f.id,
                f.email_id,
                f.user_correction,
                f.reported_at,
                f.notes,
                e.sender,
                e.subject,
                ar.classification,
                ar.risk_level
            FROM feedback f
            JOIN emails e ON f.email_id = e.id
            LEFT JOIN analysis_results ar ON e.id = ar.email_id
            WHERE e.user_email = ?
            ORDER BY f.reported_at DESC
            """,
            (user_email,),
        )
        return cursor.fetchall()


def get_metrics(user_email: str):
    """Get model performance metrics scoped to a single user."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) as total FROM analysis_results ar JOIN emails e ON ar.email_id = e.id WHERE e.user_email = ?",
            (user_email,),
        )
        total_analyzed = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) as count FROM analysis_results ar JOIN emails e ON ar.email_id = e.id WHERE ar.classification = 'phishing' AND e.user_email = ?",
            (user_email,),
        )
        phishing_count = cursor.fetchone()["count"]

        cursor.execute(
            "SELECT COUNT(*) as count FROM analysis_results ar JOIN emails e ON ar.email_id = e.id WHERE ar.classification = 'legitimate' AND e.user_email = ?",
            (user_email,),
        )
        legitimate_count = cursor.fetchone()["count"]

        cursor.execute(
            """
            SELECT COUNT(*) as count FROM feedback f
            JOIN analysis_results ar ON f.email_id = ar.email_id
            JOIN emails e ON ar.email_id = e.id
            WHERE f.user_correction = 'legitimate' AND ar.classification = 'phishing'
            AND e.user_email = ?
            """,
            (user_email,),
        )
        false_positives = cursor.fetchone()["count"]

        cursor.execute(
            """
            SELECT COUNT(*) as count FROM feedback f
            JOIN analysis_results ar ON f.email_id = ar.email_id
            JOIN emails e ON ar.email_id = e.id
            WHERE f.user_correction = 'phishing' AND ar.classification = 'legitimate'
            AND e.user_email = ?
            """,
            (user_email,),
        )
        false_negatives = cursor.fetchone()["count"]

        return {
            "total_analyzed": total_analyzed,
            "phishing_count": phishing_count,
            "legitimate_count": legitimate_count,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
        }


# Initialize database on import
if not os.path.exists(DATABASE_PATH):
    init_db()
