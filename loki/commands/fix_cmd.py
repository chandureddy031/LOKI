"""loki fix command."""

import os
import re
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm

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


def _is_fixable(error) -> bool:
    """Check if error is fixable."""
    val = _get_attr(error, 'fixable')
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ('true', '1', 'yes')
    return False


def _extract_code_from_response(response: str) -> str:
    """Extract code from AI response."""
    code_block_match = re.search(r'```(?:\w+)?\n(.*?)```', response, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1).strip()

    lines = response.strip().split('\n')
    code_lines = []
    in_code = False

    for line in lines:
        if line.startswith('```'):
            in_code = not in_code
            continue
        if in_code or (not line.startswith(('Here', 'The', 'This', 'Error', 'To fix', 'The fix', '```'))):
            code_lines.append(line)

    return '\n'.join(code_lines).strip()


def _apply_fix_to_file(file_path: Path, line_num: int, new_code: str) -> bool:
    """Apply fix to file at specific line."""
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        line_idx = int(line_num) - 1

        if line_idx < 0 or line_idx >= len(lines):
            return False

        original_line = lines[line_idx]

        new_lines = new_code.split("\n")

        lines[line_idx:line_idx + 1] = new_lines

        file_path.write_text("\n".join(lines), encoding="utf-8")
        return True

    except Exception as e:
        console.print(f"[red]Error applying fix: {e}[/red]")
        return False


def execute_fix(dry_run: bool = False, file: str = None) -> None:
    """AI-powered fix suggestions."""
    cache = CacheManager(os.getcwd())

    if not cache.exists():
        console.print("[yellow]No cache found. Run `loki init` first.[/yellow]")
        return

    errors = cache.load_errors()
    fixable = [e for e in errors if _is_fixable(e)]

    if file:
        fixable = [e for e in fixable if _get_attr(e, 'file') == file]

    if not fixable:
        console.print("[green]No fixable errors found.[/green]")
        return

    config = ConfigManager()
    secret_manager = SecretManager()
    api_key = secret_manager.retrieve_key(config.get_provider())

    if not api_key:
        console.print("[yellow]AI features require API key. Run `loki models`.[/yellow]")
        return

    from ..ai.providers import GroqProvider
    provider = GroqProvider(api_key, config.get_model())

    root_dir = Path.cwd()
    applied_count = 0

    for error in fixable:
        err_file = _get_attr(error, 'file')
        err_line = _get_attr(error, 'line')
        err_msg = _get_attr(error, 'message')

        file_path = root_dir / err_file
        if not file_path.exists():
            continue

        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        start = max(0, int(err_line) - 5)
        end = min(len(lines), int(err_line) + 5)
        context = "\n".join(lines[start:end])

        prompt = f"""Fix this error:
File: {err_file}
Line: {err_line}
Error: {err_msg}

Current code around error:
{context}

Provide ONLY the fixed code that should replace line {err_line}. No explanation."""

        response = provider.chat(prompt, [])

        console.print(f"\n[bold cyan]{err_file}:{err_line}[/bold cyan]")
        console.print(f"[red]Error:[/red] {err_msg}")

        fixed_code = _extract_code_from_response(response)
        console.print(f"[green]Suggested fix:[/green]\n{fixed_code}")

        if not dry_run:
            if Confirm.ask("Apply this fix?"):
                if _apply_fix_to_file(file_path, err_line, fixed_code):
                    console.print("[green]Fix applied successfully![/green]")
                    applied_count += 1
                else:
                    console.print("[red]Failed to apply fix[/red]")

    if applied_count > 0:
        console.print(f"\n[green]Applied {applied_count} fix(es). Run `loki init` to re-scan.[/green]")
