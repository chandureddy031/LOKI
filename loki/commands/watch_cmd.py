"""loki watch command."""

import os
import time
from pathlib import Path

from rich.console import Console
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..core.config import ConfigManager
from ..commands.init_cmd import execute_init


console = Console()


class ChangeHandler(FileSystemEventHandler):
    """Handle file changes."""

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.config = ConfigManager()

    def on_modified(self, event):
        if event.is_directory:
            return

        ext = Path(event.src_path).suffix
        if ext in self.config.get_extensions():
            console.print(f"[yellow]Changed: {event.src_path}[/yellow]")
            execute_init(self.root_dir)


def execute_watch(interval: int = 5) -> None:
    """Watch files for changes."""
    root_dir = os.getcwd()
    handler = ChangeHandler(root_dir)
    observer = Observer()
    observer.schedule(handler, root_dir, recursive=True)

    console.print("[bold]Watching for changes...[/bold]")
    console.print("Press Ctrl+C to stop.\n")

    observer.start()
    try:
        while True:
            time.sleep(interval)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
    console.print("[yellow]Stopped watching.[/yellow]")
