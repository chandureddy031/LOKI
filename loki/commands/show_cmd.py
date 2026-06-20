"""loki show command."""

import os
from ..core.cache import CacheManager
from ..core.config import ConfigManager
from ..ai.rag import RAGEngine
from ..ui.server import UIServer
from ..security.secret_manager import SecretManager


def execute_show(port: int = 8080) -> None:
    """Open web UI."""
    cache = CacheManager(os.getcwd())

    if not cache.exists():
        print("No cache found. Run `loki init` first.")
        return

    config = ConfigManager()
    secret_manager = SecretManager()

    provider_name = config.get_provider()
    api_key = secret_manager.retrieve_key(provider_name)

    if not api_key:
        print(f"No API key found. Run `loki models` to set up {provider_name}.")
        return

    from ..ai.providers import GroqProvider
    provider = GroqProvider(api_key, config.get_model())

    rag = RAGEngine(cache.get_cache_dir())

    server = UIServer(cache, rag, provider)
    server.start(port)
