from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class EmailScanRequest(BaseModel):
    """Request model for email scanning."""
    gmail_id: str
    sender: str
    subject: str
    body: str
    received_at: str
    user_email: str


class AnalysisResult(BaseModel):
    """Analysis result for an email."""
    classification: str
    confidence_score: float
    risk_level: str
    warning_signs: List[str]
    explanation: str


class EmailAnalysisResponse(BaseModel):
    """Response with email and analysis result."""
    email_id: int
    gmail_id: str
    sender: str
    subject: str
    body: str
    received_at: str
    user_email: str
    classification: str
    confidence_score: float
    risk_level: str
    warning_signs: List[str]
    explanation: str
    analyzed_at: Optional[str] = None


class FeedbackRequest(BaseModel):
    """Feedback from user on an email analysis."""
    email_id: int
    user_correction: str  # "phishing" or "legitimate"
    notes: Optional[str] = None


class MetricsResponse(BaseModel):
    """Model performance metrics."""
    total_analyzed: int
    phishing_count: int
    legitimate_count: int
    false_positives: int
    false_negatives: int
