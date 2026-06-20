"""Web UI server."""

import webbrowser
from pathlib import Path
from threading import Timer

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ..core.cache import CacheManager
from ..ai.rag import RAGEngine
from .routes import create_router


class UIServer:
    """FastAPI server for web UI."""

    def __init__(self, cache: CacheManager, rag: RAGEngine, provider):
        self.app = FastAPI(title="Loki UI")
        self.cache = cache
        self.rag = rag
        self.provider = provider
        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self) -> None:
        """Configure middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost",
                "http://localhost:8080",
                "http://127.0.0.1",
                "http://127.0.0.1:8080",
            ],
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
            allow_credentials=True,
        )

    def _setup_routes(self) -> None:
        """Register routes."""
        router = create_router(self.cache, self.rag, self.provider)
        self.app.include_router(router)

        static_dir = Path(__file__).parent / "static"
        self.app.mount("/", StaticFiles(directory=str(static_dir), html=True))

    def start(self, port: int = 8080) -> None:
        """Start server and open browser."""
        import uvicorn

        Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}")).start()
        uvicorn.run(self.app, host="127.0.0.1", port=port)
