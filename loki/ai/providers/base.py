"""Abstract AI provider."""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Base class for AI providers."""

    @abstractmethod
    def chat(self, message: str, context: list[str]) -> str:
        """Send chat message with context."""
        pass

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings."""
        pass

    @abstractmethod
    def validate_key(self, api_key: str) -> bool:
        """Validate API key."""
        pass
