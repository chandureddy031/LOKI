"""Tests for security."""

from loki.security.leak_prevention import LeakPrevention


def test_sanitize_api_key():
    """Test API key sanitization."""
    text = 'api_key = "gsk_abc123def456ghi789jkl012mno345pqr678stu901"'
    sanitized = LeakPrevention.sanitize(text)
    assert "gsk_" not in sanitized
    assert "[REDACTED]" in sanitized


def test_sanitize_for_ai():
    """Test AI sanitization."""
    text = 'password = "secret123"'
    sanitized = LeakPrevention.sanitize_for_ai(text)
    assert "secret123" not in sanitized
