"""Interactive chat session."""

import time

from ..core.types import ChatMessage
from ..security.leak_prevention import LeakPrevention
from .guardrails import AIGuardrails
from .providers.base import AIProvider
from .rag import RAGEngine


class ChatSession:
    """Manages interactive chat."""

    def __init__(self, rag: RAGEngine, provider: AIProvider, errors: list = None, files: list = None):
        self.rag = rag
        self.provider = provider
        self.errors = errors or []
        self.files = files or []
        self.history: list[ChatMessage] = []

    def send(self, message: str) -> str:
        """Send message and get response."""
        is_valid, reason = AIGuardrails.validate_input(message)
        if not is_valid:
            return f"Error: {reason}"

        sanitized = LeakPrevention.sanitize_for_ai(message)
        context = self.get_context(sanitized)
        error_context = self.get_error_context()

        full_context = context + error_context

        if hasattr(self.provider, 'set_history'):
            history_dicts = [
                {"role": msg.role, "content": msg.content}
                for msg in self.history[-10:]
            ]
            self.provider.set_history(history_dicts)

        response = self.provider.chat(sanitized, full_context)
        filtered_response = AIGuardrails.validate_output(response)

        self.history.append(ChatMessage(
            role="user",
            content=sanitized,
            timestamp=time.time(),
        ))
        self.history.append(ChatMessage(
            role="assistant",
            content=filtered_response,
            timestamp=time.time(),
            context=full_context,
        ))

        return filtered_response

    def get_context(self, message: str) -> list[str]:
        """Retrieve relevant code via RAG."""
        chunks = self.rag.query(message)
        return [f"{c.file_path}:{c.start_line}-{c.end_line}\n{c.content}" for c in chunks]

    def get_error_context(self) -> list[str]:
        """Get error context for AI."""
        context = []

        if self.errors:
            error_lines = []
            for e in self.errors[:20]:
                if isinstance(e, dict):
                    file = e.get('file', '')
                    line = e.get('line', '')
                    msg = e.get('message', '')
                    sev = e.get('severity', '')
                    error_lines.append(f"- {file}:{line} [{sev}] {msg}")
                else:
                    error_lines.append(f"- {e.file}:{e.line} [{e.severity}] {e.message}")

            if error_lines:
                context.append("DETECTED ERRORS:\n" + "\n".join(error_lines))

        if self.files:
            file_list = []
            for f in self.files[:10]:
                if isinstance(f, dict):
                    file_list.append(f.get('path', ''))
                else:
                    file_list.append(f.path if hasattr(f, 'path') else str(f))
            context.append("PROJECT FILES:\n" + "\n".join(f"- {f}" for f in file_list))

        return context

    def clear_history(self) -> None:
        """Clear chat history."""
        self.history.clear()
