"""loki errors command."""

import os
from rich.console import Console
from rich.table import Table

from ..core.cache import CacheManager


console = Console()


def _get_severity(error) -> str:
    """Get severity as string regardless of type."""
    if hasattr(error, 'severity'):
        sev = error.severity
        return sev.value if hasattr(sev, 'value') else str(sev)
    if isinstance(error, dict):
        sev = error.get('severity', 'unknown')
        return sev if isinstance(sev, str) else str(sev)
    return "unknown"


def _get_attr(error, attr: str):
    """Get attribute from error object or dict."""
    if hasattr(error, attr):
        return getattr(error, attr)
    if isinstance(error, dict):
        return error.get(attr, "")
    return ""


def execute_errors(format: str = "table", severity: str = None) -> None:
    """Show detected errors."""
    cache = CacheManager(os.getcwd())

    if not cache.exists():
        console.print("[yellow]No cache found. Run `loki init` first.[/yellow]")
        return

    errors = cache.load_errors()

    if severity:
        errors = [e for e in errors if _get_severity(e) == severity]

    if not errors:
        console.print("[green]No errors found![/green]")
        return

    if format == "json":
        import json
        from dataclasses import asdict
        print(json.dumps([asdict(e) if hasattr(e, '__dataclass_fields__') else e for e in errors], indent=2))
        return

    table = Table(title="Errors")
    table.add_column("File", style="cyan")
    table.add_column("Line", style="yellow")
    table.add_column("Severity", style="bold")
    table.add_column("Message")

    for error in errors:
        sev = _get_severity(error)
        style = {"error": "red", "warning": "yellow", "info": "blue"}.get(sev, "white")
        sev_text = f"[{style}]{sev.upper()}[/{style}]"
        table.add_row(
            str(_get_attr(error, 'file')),
            str(_get_attr(error, 'line')),
            sev_text,
            str(_get_attr(error, 'message')),
        )

    console.print(table)
