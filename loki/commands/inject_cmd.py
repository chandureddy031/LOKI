"""loki inject command - inject error capture into Python files."""

import os
import re
from pathlib import Path
from rich.console import Console

from ..core.cache import CacheManager


console = Console()

HOOK_CODE = '''
# --- Loki Error Capture Hook ---
import sys
from pathlib import Path

def _loki_log_error(exc_type, exc_value, exc_tb):
    try:
        _loki_cache = Path.home() / ".loki"
        for d in _loki_cache.iterdir():
            if d.is_dir() and len(d.name) == 12:
                _loki_errors = d / "runtime_errors.json"
                import json, threading
                from datetime import datetime

                _loki_file = exc_tb.tb_frame.f_code.co_filename if exc_tb and exc_tb.tb_frame else "unknown"
                _loki_line = exc_tb.tb_lineno if exc_tb else 0

                _entry = {
                    "timestamp": datetime.now().isoformat(),
                    "file": _loki_file,
                    "line": _loki_line,
                    "type": exc_type.__name__ if exc_type else "Unknown",
                    "message": str(exc_value),
                    "traceback": "".join(__import__("traceback").format_exception(exc_type, exc_value, exc_tb)),
                    "source": "injected",
                }

                _lock = threading.Lock()
                with _lock:
                    _errors = []
                    if _loki_errors.exists():
                        try:
                            with open(_loki_errors) as f:
                                _errors = json.load(f).get("errors", [])
                        except: pass
                    _errors.append(_entry)
                    if len(_errors) > 1000: _errors = _errors[-1000:]
                    with open(_loki_errors, "w") as f:
                        json.dump({"errors": _errors}, f, indent=2)
                break
    except: pass

sys.excepthook = _loki_log_error
# --- End Loki Hook ---
'''


def execute_inject(path: str = ".") -> None:
    """Inject error capture hook into Python files."""
    cache = CacheManager(os.getcwd())

    if not cache.exists():
        console.print("[yellow]No cache found. Run `loki init` first.[/yellow]")
        return

    root_dir = Path(path).resolve()
    injected = 0
    skipped = 0

    console.print(f"[bold]Injecting Loki hook into: {root_dir}[/bold]\n")

    for py_file in root_dir.rglob("*.py"):
        if "__pycache__" in str(py_file) or ".venv" in str(py_file):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")

            if "# --- Loki Error Capture Hook ---" in content:
                skipped += 1
                continue

            if content.strip():
                new_content = HOOK_CODE + "\n" + content
                py_file.write_text(new_content, encoding="utf-8")
                injected += 1
                console.print(f"  [green]Injected:[/green] {py_file.relative_to(root_dir)}")

        except (OSError, UnicodeDecodeError) as e:
            console.print(f"  [red]Error:[/red] {py_file.relative_to(root_dir)}: {e}")

    console.print(f"\n[green]Done![/green] Injected: {injected}, Skipped: {skipped}")
    console.print("[yellow]Run your app - all exceptions will now be captured.[/yellow]")
