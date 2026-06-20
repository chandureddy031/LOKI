"""Prevent sensitive data from leaking."""

import re


class LeakPrevention:
    """Sanitizes sensitive data."""

    SENSITIVE_PATTERNS = [
        r"(?:api[_-]?key|apikey)\s*[=:]\s*['\"]?[a-zA-Z0-9\-_]{20,}",
        r"(?:password|passwd|pwd)\s*[=:]\s*['\"]?[^\s'\"]{8,}",
        r"(?:secret|token)\s*[=:]\s*['\"]?[a-zA-Z0-9\-_]{20,}",
        r"(?:gsk_|sk-|sk-ant-)[a-zA-Z0-9]{20,}",
        r"(?:aws[_-]?access[_-]?key[_-]?id)\s*[=:]\s*[A-Z0-9]{16,}",
        r"(?:bearer)\s+[a-zA-Z0-9\-_.]+",
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Remove sensitive data from text."""
        sanitized = text
        for pattern in cls.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)
        return sanitized

    @classmethod
    def sanitize_for_ai(cls, text: str) -> str:
        """Sanitize code before sending to AI."""
        sanitized = cls.sanitize(text)
        sanitized = re.sub(r"os\.environ\[.+\]", "os.environ[...]", sanitized)
        sanitized = re.sub(r"os\.getenv\(.+\)", "os.getenv(...)", sanitized)
        return sanitized
