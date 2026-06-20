"""loki capture command - capture errors from any language/process."""

import os
import re
import sys
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table

from ..core.cache import CacheManager
from ..core.runtime_capture import setup_runtime_capture, clear_runtime_errors


console = Console()

ERROR_PATTERNS = [
    r"error\[E\d+\]",
    r"error\[",
    r"thread .* panicked",
    r"fatal:",
    r"FATAL",
    r"panic:",
    r"Error:",
    r"ERROR",
    r"Exception",
    r"Traceback",
    r"SyntaxError",
    r"NameError",
    r"TypeError",
    r"ValueError",
    r"ImportError",
    r"ModuleNotFoundError",
    r"AttributeError",
    r"KeyError",
    r"IndexError",
    r"Segmentation fault",
    r"SIGSEGV",
    r"abort",
    r"FAILED",
    r"BUILD FAILED",
    r"compilation failed",
    r"error: ",
    r"warning: ",
    r"ERR!",
    r"ERR ",
    r"\[ERROR\]",
    r"\[FATAL\]",
    r"segmentation fault",
    r"stack trace",
    r"uncaught",
    r"unhandled",
    r"cannot find symbol",
    r"NullPointer",
    r"OutOfMemory",
    r"StackOverflow",
    r"errno:",
    r"fatal error",
    r"LINK ERROR",
    r"ld:",
    r"undefined reference",
]


def _is_error_line(line: str) -> bool:
    """Check if line looks like an error from any language."""
    for pattern in ERROR_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False


def _monitor_stream(stream, label: str, errors_list: list):
    """Monitor a stream for errors."""
    try:
        for line in iter(stream.readline, ''):
            if not line:
                break
            line = line.rstrip('\n').rstrip('\r')
            if line:
                if _is_error_line(line):
                    errors_list.append({
                        "timestamp": datetime.now().isoformat(),
                        "file": "",
                        "line": 0,
                        "type": "CONSOLE_ERROR",
                        "message": line,
                        "traceback": "",
                        "source": f"console_{label}",
                    })
                    sys.stderr.write(f"\033[91m{line}\033[0m\n")
                    sys.stderr.flush()
                else:
                    if label == "stdout":
                        sys.stdout.write(line + "\n")
                        sys.stdout.flush()
                    else:
                        sys.stderr.write(line + "\n")
                        sys.stderr.flush()
    except Exception:
        pass


def _monitor_log_files(cache_dir: Path, errors_list: list):
    """Monitor common log files for errors."""
    log_patterns = [
        "*.log",
        "logs/*.log",
        "log/*.log",
        "*.err",
        "stderr*",
    ]

    seen_files = set()

    for pattern in log_patterns:
        for log_file in Path(".").glob(pattern):
            if log_file.is_file() and log_file not in seen_files:
                seen_files.add(log_file)
                try:
                    content = log_file.read_text(encoding="utf-8", errors="ignore")
                    for line in content.split("\n")[-100:]:
                        if _is_error_line(line):
                            errors_list.append({
                                "timestamp": datetime.now().isoformat(),
                                "file": str(log_file),
                                "line": 0,
                                "type": "LOG_ERROR",
                                "message": line[:500],
                                "traceback": "",
                                "source": "log_file",
                            })
                except (OSError, UnicodeDecodeError):
                    pass


def execute_capture(command: str = None) -> None:
    """Capture errors from any language/process."""
    cache = CacheManager(os.getcwd())

    if not cache.exists():
        console.print("[yellow]No cache found. Run `loki init` first.[/yellow]")
        return

    setup_runtime_capture(cache.get_cache_dir())
    clear_runtime_errors()

    if not command:
        console.print("[bold]Loki Console Capture[/bold]\n")
        console.print("[cyan]Captures errors from ANY language:[/cyan]")
        console.print("  Python, JavaScript, TypeScript, Rust, C, C++")
        console.print("  Java, Go, Ruby, PHP, Erlang, Elixir, and more\n")
        console.print("[cyan]Usage:[/cyan]")
        console.print("  loki capture python app.py")
        console.print("  loki capture node server.js")
        console.print("  loki capture cargo run")
        console.print("  loki capture gcc main.c && ./a.out")
        console.print("  loki capture javac Main.java && java Main")
        console.print("  loki capture go run main.go")
        console.print("  loki capture mix run")

        console.print("\n[yellow]Also scans log files: *.log, logs/*.log[/yellow]")
        return

    errors_list = []

    console.print(f"[bold green]Capturing:[/bold green] {command}")
    console.print("[yellow]Press Ctrl+C to stop[/yellow]\n")

    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stdout_thread = threading.Thread(
            target=_monitor_stream,
            args=(process.stdout, "stdout", errors_list),
            daemon=True,
        )
        stderr_thread = threading.Thread(
            target=_monitor_stream,
            args=(process.stderr, "stderr", errors_list),
            daemon=True,
        )

        stdout_thread.start()
        stderr_thread.start()

        process.wait()

        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)

    except KeyboardInterrupt:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
        console.print("\n[yellow]Capture stopped.[/yellow]")

    _monitor_log_files(cache.get_cache_dir(), errors_list)

    console.print(f"\n[bold]{'='*60}[/bold]")
    console.print(f"[bold]Capture Summary: {len(errors_list)} error(s) found[/bold]")
    console.print(f"[bold]{'='*60}[/bold]\n")

    if errors_list:
        table = Table(title="Captured Errors (All Languages)")
        table.add_column("#", style="dim", width=4)
        table.add_column("Time", style="cyan", width=10)
        table.add_column("Source", style="green", width=12)
        table.add_column("Message")

        for i, err in enumerate(errors_list[-50:], 1):
            ts = err.get("timestamp", "")[-8:]
            source = err.get("source", "unknown")
            msg = err.get("message", "")[:120]

            table.add_row(
                str(i),
                ts,
                source,
                f"[red]{msg}[/red]",
            )

        console.print(table)

        save_path = cache.get_cache_dir() / "runtime_errors.json"
        import json
        with open(save_path, "w") as f:
            json.dump({"errors": errors_list}, f, indent=2)

        console.print("\n[green]Errors saved to cache for AI analysis.[/green]")
    else:
        console.print("[green]No errors captured.[/green]")
