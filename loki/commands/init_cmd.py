"""loki init command."""

from pathlib import Path

from rich.console import Console
from rich.progress import Progress

from ..core.scanner import FileScanner
from ..core.errors import ErrorDetector
from ..core.cache import CacheManager
from ..core.config import ConfigManager
from ..core.runtime_capture import setup_runtime_capture, get_runtime_errors
from ..core.global_hook import init_hook as init_global_hook
from ..ai.rag import RAGEngine


console = Console()


def execute_init(path: str = ".") -> None:
    """Scan codebase and build cache."""
    root_dir = Path(path).resolve()

    if not root_dir.exists():
        console.print(f"[red]Error: Path {path} does not exist[/red]")
        return

    config = ConfigManager()
    cache = CacheManager(str(root_dir))

    setup_runtime_capture(cache.get_cache_dir())
    init_global_hook(cache.get_cache_dir())

    with Progress() as progress:
        task = progress.add_task("Scanning files...", total=None)

        scanner = FileScanner(str(root_dir), config.get_ignore_patterns())
        scan_result = scanner.scan()

        progress.update(task, description="Detecting errors...")
        detector = ErrorDetector(scan_result, str(root_dir))
        errors = detector.detect_all()

        progress.update(task, description="Loading runtime errors...")
        runtime_errors = get_runtime_errors()

        progress.update(task, description="Building index...")
        rag = RAGEngine(cache.get_cache_dir())
        chunks = []
        for file_meta in scan_result.files:
            if file_meta.language.value != "unknown":
                file_path = root_dir / file_meta.path
                try:
                    content = file_path.read_text(encoding="utf-8")
                    file_chunks = rag.chunk_code(file_meta.path, content, file_meta.language)
                    chunks.extend(file_chunks)
                except (OSError, UnicodeDecodeError):
                    continue

        if chunks:
            rag.build_index(chunks)

        progress.update(task, description="Saving cache...")
        cache.save_scan(scan_result)
        cache.save_errors(errors)

    summary = detector.get_summary()
    console.print("\n[green]Scan complete![/green]")
    console.print(f"Files scanned: {len(scan_result.files)}")
    console.print(f"Errors found: {summary.errors}")
    console.print(f"Warnings: {summary.warnings}")
    console.print(f"Info: {summary.info}")

    if runtime_errors:
        console.print(f"[yellow]Runtime errors captured: {len(runtime_errors)}[/yellow]")
