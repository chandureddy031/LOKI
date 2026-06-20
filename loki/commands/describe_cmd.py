"""loki describe command."""

import os
from rich.console import Console
from rich.markdown import Markdown

from ..core.cache import CacheManager
from ..core.config import ConfigManager
from ..security.secret_manager import SecretManager


console = Console()


def _get_attr(error, attr: str):
    """Get attribute from error object or dict."""
    if hasattr(error, attr):
        return getattr(error, attr)
    if isinstance(error, dict):
        return error.get(attr, "")
    return ""


def execute_describe(file: str = None) -> None:
    """Describe errors in detail."""
    cache = CacheManager(os.getcwd())

    if not cache.exists():
        console.print("[yellow]No cache found. Run `loki init` first.[/yellow]")
        return

    errors = cache.load_errors()

    if file:
        errors = [e for e in errors if _get_attr(e, 'file') == file]

    if not errors:
        console.print("[green]No errors to describe.[/green]")
        return

    config = ConfigManager()
    secret_manager = SecretManager()
    api_key = secret_manager.retrieve_key(config.get_provider())

    if not api_key:
        console.print("[yellow]AI features require API key. Run `loki models`.[/yellow]")
        return

    from ..ai.providers import GroqProvider
    provider = GroqProvider(api_key, config.get_model())

    for error in errors:
        err_file = _get_attr(error, 'file')
        err_line = _get_attr(error, 'line')
        err_msg = _get_attr(error, 'message')
        err_code = _get_attr(error, 'code')

        prompt = f"""Describe this error in detail:
File: {err_file}
Line: {err_line}
Error: {err_msg}
Code: {err_code}

Provide:
1. What this error means
2. Why it happened
3. How to fix it with code example"""

        response = provider.chat(prompt, [])
        console.print(f"\n[bold cyan]{err_file}:{err_line}[/bold cyan]")
        console.print(Markdown(response))
