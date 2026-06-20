"""loki exit command."""

import os
from rich.console import Console
from rich.prompt import Confirm

from ..core.cache import CacheManager


console = Console()


def execute_exit(force: bool = False) -> None:
    """Clear project cache."""
    cache = CacheManager(os.getcwd())

    if not cache.exists():
        console.print("[yellow]No cache found.[/yellow]")
        return

    if not force:
        if not Confirm.ask("Delete all cached data for this project?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    cache.clear()
    console.print("[green]Project memory cleared.[/green]")
