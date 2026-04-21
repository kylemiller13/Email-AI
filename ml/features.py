"""
Engineered feature extraction for phishing detection.

Features fall into four groups:
  1. URL/Link  — malicious or suspicious links
  2. Sender    — spoofed or mismatched sender identity
  3. Content   — urgency, credential requests, generic greetings
  4. Structural — HTML patterns, attachments, formatting abuse
"""

import re
from typing import Dict, List, Tuple
import numpy as np

# ---------------------------------------------------------------------------
# Word lists
# ---------------------------------------------------------------------------

URGENCY_WORDS = {
    "urgent", "immediately", "expire", "expires", "expiring", "expired",
    "suspended", "suspend", "verify", "verification", "confirm", "confirmation",
    "act now", "act immediately", "limited time", "last chance", "final notice",
    "action required", "response required", "24 hours", "48 hours", "deadline",
    "warning", "alert", "important notice", "your account", "account restricted",
}

CREDENTIAL_WORDS = {
    "password", "passwd", "passcode", "pin", "ssn", "social security",
    "credit card", "card number", "cvv", "bank account", "routing number",
    "date of birth", "dob", "mother's maiden", "security question",
    "username", "login credentials", "sign in details",
}

THREAT_PHRASES = {
    "will be closed", "will be suspended", "will be terminated", "will be deleted",
    "legal action", "law enforcement", "prosecuted", "reported to",
    "lose access", "account has been", "account was", "unusual activity",
    "unauthorized access", "suspicious activity",
}

MONEY_WORDS = {
    "lottery", "winner", "won", "prize", "million dollars", "million usd",
    "inheritance", "beneficiary", "funds transfer", "wire transfer",
    "western union", "money gram", "bitcoin", "cryptocurrency", "investment",
    "claim your", "free money", "cash prize", "reward",
}

GENERIC_GREETINGS = re.compile(
    r"\b(dear\s+(customer|user|account\s*holder|valued\s*customer|member|client|sir|madam|friend)|"
    r"hello\s+(customer|user|member)|greetings\s+from)\b",
    re.IGNORECASE,
)

SHORTENED_URL_DOMAINS = {
    "bit.ly", "tinyurl.com", "t.co", "ow.ly", "goo.gl", "buff.ly",
    "short.io", "rebrand.ly", "cutt.ly", "is.gd", "v.gd", "shorte.st",
}

SUSPICIOUS_TLDS = {".xyz", ".tk", ".ml", ".ga", ".cf", ".gq", ".top", ".click", ".loan", ".work"}

FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "mail.com", "ymail.com", "live.com", "msn.com", "protonmail.com",
}

CREDENTIAL_URL_KEYWORDS = {
    "login", "signin", "sign-in", "verify", "verification", "account",
    "update", "confirm", "secure", "banking", "webscr", "password",
}

ATTACHMENT_WORDS = re.compile(
    r"\b(see\s+attached|open\s+the\s+(document|file|attachment)|"
    r"attached\s+(file|document|invoice|report)|download\s+(the\s+)?(file|document))\b",
    re.IGNORECASE,
)

URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
HTML_TAG_PATTERN = re.compile(r"<[^>]+>", re.IGNORECASE)
IP_URL_PATTERN = re.compile(r"https?://\d{1,3}(\.\d{1,3}){3}", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Feature names — keep in sync with extract_features() return order
# ---------------------------------------------------------------------------

FEATURE_NAMES = [
    # URL features
    "url_count",
    "has_ip_url",
    "has_shortened_url",
    "suspicious_tld",
    "url_credential_keyword",
    "http_only_links",
    # Sender features
    "free_email_sender",
    "numeric_chars_in_sender_domain",
    "sender_domain_mismatch",
    # Content features
    "urgency_word_count",
    "credential_request",
    "generic_greeting",
    "threat_language",
    "money_language",
    "caps_ratio",
    "exclamation_count",
    "subject_urgency",
    # Structural features
    "html_tag_count",
    "has_form_tag",
    "has_script_tag",
    "attachment_reference",
    "body_length_log",
]

# Human-readable label for each feature when it fires
FEATURE_LABELS: Dict[str, str] = {
    "url_count":                   "Contains multiple URLs",
    "has_ip_url":                  "URL uses raw IP address instead of domain",
    "has_shortened_url":           "Contains shortened/obfuscated URL",
    "suspicious_tld":              "URL with suspicious top-level domain (.xyz, .tk, etc.)",
    "url_credential_keyword":      "URL contains credential/login keyword",
    "http_only_links":             "Uses insecure HTTP links (not HTTPS)",
    "free_email_sender":           "Sent from a free email provider (Gmail, Yahoo, etc.)",
    "numeric_chars_in_sender_domain": "Sender domain contains unusual numbers or hyphens",
    "sender_domain_mismatch":      "Sender display name doesn't match email domain",
    "urgency_word_count":          "Contains urgency language",
    "credential_request":          "Requests credentials or sensitive personal info",
    "generic_greeting":            "Uses generic greeting (Dear Customer, Dear User)",
    "threat_language":             "Contains threatening language about account suspension",
    "money_language":              "Contains money/prize/lottery language",
    "caps_ratio":                  "Excessive use of capital letters",
    "exclamation_count":           "Excessive exclamation marks",
    "subject_urgency":             "Subject line contains urgency words",
    "html_tag_count":              "Heavy use of HTML formatting",
    "has_form_tag":                "Contains an HTML form (credential harvesting)",
    "has_script_tag":              "Contains JavaScript",
    "attachment_reference":        "References a file attachment",
    "body_length_log":             "Unusually short or long email body",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_urls(text: str) -> List[str]:
    return URL_PATTERN.findall(text)


def _url_domain(url: str) -> str:
    match = re.match(r"https?://([^/?\s]+)", url, re.IGNORECASE)
    return match.group(1).lower() if match else ""


def _sender_domain(sender: str) -> str:
    match = re.search(r"@([\w.\-]+)", sender)
    return match.group(1).lower() if match else ""


def _sender_display_name(sender: str) -> str:
    # "Google <noreply@google.com>" → "Google"
    match = re.match(r"^([^<@]+)<", sender)
    if match:
        return match.group(1).strip().lower()
    return ""


# ---------------------------------------------------------------------------
# Core extractor
# ---------------------------------------------------------------------------

def extract_features(
    body: str,
    subject: str = "",
    sender: str = "",
) -> Tuple[np.ndarray, List[str]]:
    """
    Returns (feature_vector, fired_warning_labels).

    feature_vector   — 1-D float array matching FEATURE_NAMES order
    fired_warnings   — human-readable strings for features that fired
    """
    body = str(body) if body else ""
    subject = str(subject) if subject else ""
    sender = str(sender) if sender else ""
    full_text = subject + " " + body

    # -- URL features --------------------------------------------------------
    urls = _extract_urls(full_text)
    url_count = len(urls)

    has_ip_url = int(bool(IP_URL_PATTERN.search(full_text)))

    has_shortened_url = int(
        any(_url_domain(u) in SHORTENED_URL_DOMAINS for u in urls)
    )

    suspicious_tld = int(
        any(
            any(_url_domain(u).endswith(tld) for tld in SUSPICIOUS_TLDS)
            for u in urls
        )
    )

    url_credential_keyword = int(
        any(
            any(kw in u.lower() for kw in CREDENTIAL_URL_KEYWORDS)
            for u in urls
        )
    )

    http_only_links = int(
        any(u.lower().startswith("http://") for u in urls) and url_count > 0
    )

    # -- Sender features -----------------------------------------------------
    sender_domain = _sender_domain(sender)
    display_name = _sender_display_name(sender)

    free_email_sender = int(sender_domain in FREE_EMAIL_DOMAINS)

    numeric_chars_in_sender_domain = int(
        bool(re.search(r"\d{2,}|(-\w+-)", sender_domain))
    )

    # Display name looks like a legitimate company but domain is free/different
    if display_name and sender_domain:
        display_words = set(re.findall(r"\w+", display_name))
        domain_words = set(re.findall(r"\w+", sender_domain.split(".")[0]))
        sender_domain_mismatch = int(
            len(display_words) > 0
            and len(display_words & domain_words) == 0
            and free_email_sender == 1
        )
    else:
        sender_domain_mismatch = 0

    # -- Content features ----------------------------------------------------
    lower_text = full_text.lower()

    urgency_word_count = sum(1 for w in URGENCY_WORDS if w in lower_text)

    credential_request = int(any(w in lower_text for w in CREDENTIAL_WORDS))

    generic_greeting = int(bool(GENERIC_GREETINGS.search(body)))

    threat_language = int(any(p in lower_text for p in THREAT_PHRASES))

    money_language = int(any(w in lower_text for w in MONEY_WORDS))

    words = re.findall(r"[A-Za-z]+", full_text)
    caps_ratio = (
        sum(1 for w in words if w.isupper() and len(w) > 1) / max(len(words), 1)
    )

    exclamation_count = min(full_text.count("!"), 10)

    subject_lower = subject.lower()
    subject_urgency = int(any(w in subject_lower for w in URGENCY_WORDS))

    # -- Structural features -------------------------------------------------
    html_tags = HTML_TAG_PATTERN.findall(body)
    html_tag_count = min(len(html_tags), 50)

    has_form_tag = int(bool(re.search(r"<\s*form\b", body, re.IGNORECASE)))

    has_script_tag = int(bool(re.search(r"<\s*script\b", body, re.IGNORECASE)))

    attachment_reference = int(bool(ATTACHMENT_WORDS.search(full_text)))

    body_length_log = float(np.log1p(len(body)))

    # -- Assemble vector -----------------------------------------------------
    vector = np.array([
        float(url_count),
        float(has_ip_url),
        float(has_shortened_url),
        float(suspicious_tld),
        float(url_credential_keyword),
        float(http_only_links),
        float(free_email_sender),
        float(numeric_chars_in_sender_domain),
        float(sender_domain_mismatch),
        float(urgency_word_count),
        float(credential_request),
        float(generic_greeting),
        float(threat_language),
        float(money_language),
        float(caps_ratio),
        float(exclamation_count),
        float(subject_urgency),
        float(html_tag_count),
        float(has_form_tag),
        float(has_script_tag),
        float(attachment_reference),
        float(body_length_log),
    ], dtype=np.float32)

    assert len(vector) == len(FEATURE_NAMES), (
        f"Vector length {len(vector)} != FEATURE_NAMES length {len(FEATURE_NAMES)}"
    )

    # -- Fired warnings (features that meaningfully activated) ---------------
    thresholds = {
        "url_count": 1,
        "urgency_word_count": 1,
        "exclamation_count": 2,
        "html_tag_count": 5,
        "caps_ratio": 0.1,
        "body_length_log": None,  # excluded — not a direct warning
    }

    fired = []
    for name, val in zip(FEATURE_NAMES, vector):
        if name == "body_length_log":
            continue
        threshold = thresholds.get(name, 0.5)
        if val > threshold:
            fired.append(FEATURE_LABELS[name])

    return vector, fired


def extract_features_from_text(text: str) -> Tuple[np.ndarray, List[str]]:
    """Convenience wrapper for training where only raw text is available."""
    return extract_features(body=text, subject="", sender="")
