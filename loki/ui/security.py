"""Web UI security."""

import time
import re
from collections import defaultdict
from html import escape


class RateLimiter:
    """In-memory rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed."""
        now = time.time()
        cutoff = now - self.window_seconds

        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if t > cutoff
        ]

        if len(self.requests[client_ip]) >= self.max_requests:
            return False

        self.requests[client_ip].append(now)
        return True


class InputSanitizer:
    """Sanitize web inputs."""

    @staticmethod
    def sanitize_file_path(file_path: str) -> str:
        """Sanitize file path."""
        import os

        path = file_path.replace("\x00", "")
        path = os.path.normpath(path)

        if ".." in path or path.startswith("/"):
            raise ValueError("Path traversal detected")

        if not re.match(r"^[a-zA-Z0-9._/-]+$", path):
            raise ValueError("Invalid characters in path")

        return path

    @staticmethod
    def sanitize_message(message: str) -> str:
        """Sanitize chat message."""
        message = escape(message)
        message = message[:10000]
        message = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", message)
        return message
