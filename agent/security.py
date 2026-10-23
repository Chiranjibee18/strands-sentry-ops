"""
Security & Input Sanitization Guardrails for Strands Sentry-Ops / DevFlow AI
----------------------------------------------------------------------------
Provides deterministic, zero-overhead pre-processing for:
1. Secret redaction (AWS keys, GitHub tokens, passwords, bearer tokens)
2. Prompt injection & directive containment
3. Input bounds & empty/oversized log validation
"""

import re
from typing import Tuple, Dict, Any


# Regex patterns for secret detection
PATTERNS = {
    "aws_access_key": re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
    "aws_secret_key": re.compile(r"(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])"),
    "github_token": re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{36,255})\b"),
    "bearer_token": re.compile(r"(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*", re.IGNORECASE),
    "password_kv": re.compile(r"(password|passwd|secret|api_key|token)\s*[:=]\s*['\"]?([^'\"\s,;&]+)['\"]?", re.IGNORECASE),
}

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous\s+)?(rules|instructions|guidelines)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous\s+)?(safety|rules|instructions)", re.IGNORECASE),
    re.compile(r"override\s+(all\s+)?safety\s+protocols?", re.IGNORECASE),
    re.compile(r"system\s+prompt\s+leak", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
]


def redact_secrets(text: str) -> Tuple[str, Dict[str, int]]:
    """
    Redacts credentials and sensitive tokens from logs before forwarding to models or logs.
    Returns:
        (sanitized_text, redaction_counts)
    """
    counts = {}
    sanitized = text

    # Redact AWS Access Keys
    matches = len(PATTERNS["aws_access_key"].findall(sanitized))
    if matches:
        counts["aws_access_key"] = matches
        sanitized = PATTERNS["aws_access_key"].sub("[REDACTED_AWS_ACCESS_KEY]", sanitized)

    # Redact GitHub Tokens
    matches = len(PATTERNS["github_token"].findall(sanitized))
    if matches:
        counts["github_token"] = matches
        sanitized = PATTERNS["github_token"].sub("[REDACTED_GITHUB_TOKEN]", sanitized)

    # Redact Bearer Tokens
    matches = len(PATTERNS["bearer_token"].findall(sanitized))
    if matches:
        counts["bearer_token"] = matches
        sanitized = PATTERNS["bearer_token"].sub(r"\1[REDACTED_BEARER_TOKEN]", sanitized)

    # Redact Key-Value Secrets
    def _kv_repl(m):
        key = m.group(1)
        return f"{key}=[REDACTED_SECRET]"
    
    matches = len(PATTERNS["password_kv"].findall(sanitized))
    if matches:
        counts["password_kv"] = matches
        sanitized = PATTERNS["password_kv"].sub(_kv_repl, sanitized)

    return sanitized, counts


def validate_input_log(log_text: str, max_length: int = 65536) -> Tuple[str, Dict[str, Any]]:
    """
    Validates log input length and content validity.
    Raises ValueError if input is empty or invalid.
    """
    if log_text is None:
        raise ValueError("Log input cannot be None.")
    
    stripped = log_text.strip()
    if not stripped:
        raise ValueError("Log input cannot be empty.")
    
    if len(stripped) < 5:
        raise ValueError("Log input is too short (< 5 characters) to contain valid diagnostic context.")

    metadata = {
        "original_length": len(log_text),
        "is_truncated": False,
    }

    if len(log_text) > max_length:
        log_text = log_text[:max_length] + "\n... [TRUNCATED: Log exceeded 64KB maximum limit]"
        metadata["is_truncated"] = True
        metadata["truncated_length"] = len(log_text)

    return log_text, metadata


def detect_prompt_injection(text: str) -> Tuple[bool, str]:
    """
    Scans log text for adversarial prompt injection phrases.
    """
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, f"Detected injection directive: '{match.group(0)}'"
    return False, ""
