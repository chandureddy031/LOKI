"""Tests for AI providers."""

from loki.ai.providers.groq import GroqProvider


def test_groq_validate_key():
    """Test Groq key validation."""
    provider = GroqProvider.__new__(GroqProvider)

    assert provider.validate_key("gsk_" + "a" * 48)
    assert not provider.validate_key("invalid_key")
    assert not provider.validate_key("sk_" + "a" * 48)
