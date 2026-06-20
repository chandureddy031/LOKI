"""API routes."""

from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..core.cache import CacheManager
from ..ai.rag import RAGEngine
from ..ai.chat import ChatSession
from .security import InputSanitizer


def create_router(cache: CacheManager, rag: RAGEngine, provider) -> APIRouter:
    """Create API router."""
    router = APIRouter()

    @router.get("/api/files")
    async def get_files():
        """Get file tree with error counts."""
        scan = cache.load_scan()
        if scan is None:
            return {"files": []}

        errors = cache.load_errors()
        error_counts = {}
        for e in errors:
            err_file = e.file if hasattr(e, 'file') else e.get('file', '')
            error_counts[err_file] = error_counts.get(err_file, 0) + 1

        files = []
        for f in scan.files:
            if isinstance(f, dict):
                path = f.get('path', '')
                lang = f.get('language', 'unknown')
                lines = f.get('lines', 0)
            else:
                path = f.path
                lang = f.language.value if hasattr(f.language, 'value') else f.language
                lines = f.lines

            files.append({
                "path": path,
                "language": lang,
                "lines": lines,
                "errors": error_counts.get(path, 0),
            })

        return {"files": files}

    @router.get("/api/errors")
    async def get_errors(file: str = None):
        """Get errors, optionally filtered by file."""
        errors = cache.load_errors()

        def _get_attr(error, attr: str):
            if hasattr(error, attr):
                return getattr(error, attr)
            if isinstance(error, dict):
                return error.get(attr, "")
            return ""

        if file:
            file = InputSanitizer.sanitize_file_path(file)
            errors = [e for e in errors if _get_attr(e, 'file') == file]

        from dataclasses import asdict
        result = []
        for e in errors:
            if hasattr(e, '__dataclass_fields__'):
                result.append(asdict(e))
            elif isinstance(e, dict):
                result.append(e)
            else:
                result.append({"error": str(e)})

        return {"errors": result}

    @router.get("/api/content")
    async def get_content(file: str):
        """Get file content."""
        file = InputSanitizer.sanitize_file_path(file)

        project_dir = cache.project_dir
        file_path = project_dir / file

        if not file_path.exists():
            return {"error": "File not found"}

        content = file_path.read_text(encoding="utf-8", errors="ignore")
        return {"content": content}

    @router.post("/api/chat")
    async def chat(message: dict):
        """Send chat message."""
        msg = InputSanitizer.sanitize_message(message.get("message", ""))

        errors = cache.load_errors()
        scan = cache.load_scan()
        files = scan.files if scan and hasattr(scan, 'files') else (scan.get('files', []) if isinstance(scan, dict) else [])

        session = ChatSession(rag, provider, errors=errors, files=files)
        response = session.send(msg)

        return {"response": response}

    @router.websocket("/ws/chat")
    async def websocket_chat(ws: WebSocket):
        """WebSocket chat."""
        await ws.accept()

        errors = cache.load_errors()
        scan = cache.load_scan()
        files = scan.files if scan and hasattr(scan, 'files') else (scan.get('files', []) if isinstance(scan, dict) else [])

        session = ChatSession(rag, provider, errors=errors, files=files)

        try:
            while True:
                data = await ws.receive_text()
                msg = InputSanitizer.sanitize_message(data)
                response = session.send(msg)
                await ws.send_text(response)
        except WebSocketDisconnect:
            pass

    @router.get("/api/runtime-errors")
    async def get_runtime_errors():
        """Get runtime errors."""
        from ..core.runtime_capture import get_runtime_errors as get_re
        errors = get_re()
        return {"errors": errors}

    return router
