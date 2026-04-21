import os
import joblib
import numpy as np
import scipy.sparse as sp
from typing import Dict
from ml.features import extract_features, FEATURE_NAMES

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

_model_data = None


def _load_model():
    global _model_data
    if _model_data is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. "
                "Please run 'python ml/train.py' first."
            )
        _model_data = joblib.load(MODEL_PATH)
    return _model_data


def predict(body: str, subject: str = "", sender: str = "") -> Dict:
    """
    Classify an email and return structured results.

    Returns:
        classification   — "phishing" or "legitimate"
        confidence_score — float 0–1 (probability of phishing)
        risk_level       — "high" | "medium" | "low"
        warning_signs    — list of human-readable fired-feature labels
        explanation      — single sentence summary
    """
    model_data = _load_model()
    model      = model_data["model"]
    vectorizer = model_data["vectorizer"]
    scaler     = model_data["scaler"]

    body    = str(body).strip()    if body    else ""
    subject = str(subject).strip() if subject else ""
    sender  = str(sender).strip()  if sender  else ""

    if not body:
        return {
            "classification": "legitimate",
            "confidence_score": 0.0,
            "risk_level": "low",
            "warning_signs": [],
            "explanation": "Empty email body.",
        }

    # Engineered features
    eng_vector, warning_signs = extract_features(body=body, subject=subject, sender=sender)
    eng_scaled = scaler.transform(eng_vector.reshape(1, -1))

    # TF-IDF background signal
    full_text   = subject + " " + body
    tfidf_mat   = vectorizer.transform([full_text])

    # Combined feature matrix (matches training layout)
    X = sp.hstack([tfidf_mat, sp.csr_matrix(eng_scaled)])

    prediction    = model.predict(X)[0]
    probabilities = model.predict_proba(X)[0]
    phishing_idx  = list(model.classes_).index("phishing")
    confidence    = float(probabilities[phishing_idx])

    if confidence >= 0.85:
        risk_level = "critical"
    elif confidence >= 0.5:
        risk_level = "warning"
    else:
        risk_level = "safe"

    # Build explanation from fired warning signs
    if prediction == "phishing":
        if warning_signs:
            explanation = (
                f"This email was classified as phishing with {round(confidence * 100)}% confidence. "
                f"{len(warning_signs)} indicator(s) detected: {'; '.join(warning_signs[:3])}."
            )
        else:
            explanation = (
                f"This email was classified as phishing with {round(confidence * 100)}% confidence "
                "based on its overall language patterns."
            )
    else:
        if warning_signs:
            explanation = (
                f"This email appears legitimate ({round((1 - confidence) * 100)}% confidence), "
                f"though {len(warning_signs)} minor indicator(s) were noted."
            )
        else:
            explanation = (
                f"This email appears legitimate with {round((1 - confidence) * 100)}% confidence. "
                "No phishing indicators detected."
            )

    return {
        "classification": prediction,
        "confidence_score": round(confidence, 4),
        "risk_level": risk_level,
        "warning_signs": warning_signs,
        "explanation": explanation,
    }


if __name__ == "__main__":
    tests = [
        {
            "subject": "URGENT: Verify your account immediately",
            "sender": "security@paypa1-alerts.xyz",
            "body": (
                "Dear Customer,\n\n"
                "Your account has been suspended due to suspicious activity. "
                "Click here immediately to verify your password and credit card details "
                "or your account will be permanently deleted within 24 hours.\n\n"
                "http://bit.ly/verify-now\n\n"
                "WARNING: Failure to act will result in legal action."
            ),
        },
        {
            "subject": "Team lunch tomorrow",
            "sender": "alice@company.com",
            "body": "Hey everyone, just a reminder about the team lunch tomorrow at noon. See you there!",
        },
    ]

    for t in tests:
        result = predict(body=t["body"], subject=t["subject"], sender=t["sender"])
        print(f"\nSubject: {t['subject']}")
        print(f"  Classification:  {result['classification']}")
        print(f"  Confidence:      {result['confidence_score']}")
        print(f"  Risk Level:      {result['risk_level']}")
        print(f"  Warning Signs:   {result['warning_signs']}")
        print(f"  Explanation:     {result['explanation']}")
