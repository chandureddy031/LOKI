"""loki report command."""

import os
from datetime import datetime
from pathlib import Path

from rich.console import Console

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


def execute_report(output: str = None) -> None:
    """Generate markdown report."""
    cache = CacheManager(os.getcwd())

    if not cache.exists():
        console.print("[yellow]No cache found. Run `loki init` first.[/yellow]")
        return

    scan = cache.load_scan()
    errors = cache.load_errors()

    files_count = 0
    if scan:
        files_count = len(scan.files) if hasattr(scan, 'files') else len(scan.get('files', []))

    report = f"""# Loki Report

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

- Files scanned: {files_count}
- Total errors: {len(errors)}

## Errors by Severity

"""

    from collections import Counter
    severity_counts = Counter(_get_severity(e) for e in errors)
    for severity, count in severity_counts.most_common():
        report += f"- {severity}: {count}\n"

    report += "\n## Errors by File\n\n"

    file_counts = Counter(_get_attr(e, 'file') for e in errors)
    for file_path, count in file_counts.most_common(10):
        report += f"- {file_path}: {count} errors\n"

    report += "\n## Error Details\n\n"

    for error in errors:
        file = _get_attr(error, 'file')
        line = _get_attr(error, 'line')
        report += f"### {file}:{line}\n\n"
        report += f"- **Severity:** {_get_severity(error)}\n"
        report += f"- **Code:** {_get_attr(error, 'code')}\n"
        report += f"- **Message:** {_get_attr(error, 'message')}\n"
        report += f"- **Source:** {_get_attr(error, 'source')}\n\n"

    output_path = output or f"loki-report-{datetime.now().strftime('%Y%m%d')}.md"
    Path(output_path).write_text(report)

    console.print(f"[green]Report saved to {output_path}[/green]")
