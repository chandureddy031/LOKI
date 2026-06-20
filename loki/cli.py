"""CLI entry point."""

import click

from loki import __version__


@click.group()
@click.version_option(__version__, prog_name="loki")
def main():
    """Loki - AI-powered code analysis CLI."""
    pass


@main.command()
@click.option("--path", default=".", help="Path to scan")
def init(path):
    """Scan codebase and build cache."""
    from loki.commands.init_cmd import execute_init
    execute_init(path)


@main.command()
@click.option("--format", "fmt", default="table", help="Output format (table/json)")
@click.option("--severity", help="Filter by severity")
def errors(fmt, severity):
    """Show detected errors."""
    from loki.commands.errors_cmd import execute_errors
    execute_errors(fmt, severity)


@main.command()
@click.option("--port", default=8080, help="Port for web UI")
def show(port):
    """Open web UI."""
    from loki.commands.show_cmd import execute_show
    execute_show(port)


@main.command()
@click.option("--file", help="Describe errors in specific file")
def describe(file):
    """Describe errors in detail."""
    from loki.commands.describe_cmd import execute_describe
    execute_describe(file)


@main.command("ai")
@click.argument("question", required=False)
def ai_cmd(question):
    """Chat with AI about your code."""
    from loki.commands.ai_cmd import execute_ai
    execute_ai(question)


@main.command(name="exit")
@click.option("--force", is_flag=True, help="Skip confirmation")
def exit_cmd(force):
    """Clear project cache."""
    from loki.commands.exit_cmd import execute_exit
    execute_exit(force)


@main.command()
@click.option("--dry-run", is_flag=True, help="Show fixes without applying")
@click.option("--file", help="Fix specific file")
def fix(dry_run, file):
    """AI-powered fix suggestions."""
    from loki.commands.fix_cmd import execute_fix
    execute_fix(dry_run, file)


@main.command()
@click.option("--interval", default=5, help="Re-scan interval (seconds)")
def watch(interval):
    """Watch files for changes."""
    from loki.commands.watch_cmd import execute_watch
    execute_watch(interval)


@main.command()
@click.option("--output", help="Output file path")
def report(output):
    """Generate markdown report."""
    from loki.commands.report_cmd import execute_report
    execute_report(output)


@main.command()
@click.option("--set", "set_provider", help="Set provider")
@click.option("--list", "list_providers", is_flag=True, help="List providers")
def models(set_provider, list_providers):
    """Manage AI providers."""
    from loki.commands.models_cmd import execute_models
    execute_models(set_provider, list_providers)


@main.command()
@click.argument("command", required=False)
def capture(command):
    """Capture console errors from running processes."""
    from loki.commands.capture_cmd import execute_capture
    execute_capture(command)


@main.command()
@click.option("--path", default=".", help="Path to inject hook")
def inject(path):
    """Inject error capture hook into Python files."""
    from loki.commands.inject_cmd import execute_inject
    execute_inject(path)
