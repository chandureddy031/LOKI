"""loki ai command."""

import os
from rich.console import Console

from ..core.cache import CacheManager
from ..core.config import ConfigManager
from ..security.secret_manager import SecretManager
from ..ai.rag import RAGEngine
from ..ai.chat import ChatSession


console = Console()


def execute_ai(single_question: str = None) -> None:
    """Interactive AI chat."""
    cache = CacheManager(os.getcwd())

    if not cache.exists():
        console.print("[yellow]No cache found. Run `loki init` first.[/yellow]")
        return

    config = ConfigManager()
    secret_manager = SecretManager()
    api_key = secret_manager.retrieve_key(config.get_provider())

    if not api_key:
        console.print("[yellow]AI features require API key. Run `loki models`.[/yellow]")
        return

    from ..ai.providers import GroqProvider
    provider = GroqProvider(api_key, config.get_model())
    rag = RAGEngine(cache.get_cache_dir())

    session = ChatSession(rag, provider)

    if single_question:
        response = session.send(single_question)
        console.print(f"\n[bold green]Loki:[/bold green] {response}")
        return

    console.print("[bold]Loki AI Chat[/bold]")
    console.print("Type your question or /exit to quit.\n")

    while True:
        try:
            user_input = console.input("[bold cyan]You:[/bold cyan] ")
        except (EOFError, KeyboardInterrupt):
            break

        if user_input.strip() in ("/exit", "/quit", "exit", "quit"):
            break

        if not user_input.strip():
            continue

        response = session.send(user_input)
        console.print(f"\n[bold green]Loki:[/bold green] {response}\n")
