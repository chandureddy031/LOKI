"""CLI entry point."""

import click

from loki import __version__


@click.group()
@click.version_option(__version__, prog_name="loki")
def main():
    """Loki - AI-powered code analysis CLI with error detection and chat."""
    pass


@main.command(short_help="Scan codebase and build cache")
@click.option("--path", default=".", help="Path to scan")
def init(path):
    """Scan codebase and build cache.

    Scans the project directory for Python files, detects errors using
    static analysis and AI, builds a search index for the chat feature,
    and saves results to the local cache.

    \b
    OPTIONS:
      --path PATH    Path to scan (default: current directory)

    \b
    EXAMPLES:
      loki init                    Scan current directory
      loki init --path ./src       Scan specific folder
      loki init --path /project    Scan absolute path

    \b
    NOTES:
      - Run this command first before using other loki commands
      - Re-run after major code changes to update the cache
      - Cache is stored in .loki/ directory and can be cleared with loki exit
    """
    from loki.commands.init_cmd import execute_init
    execute_init(path)


@main.command(short_help="Show detected errors")
@click.option("--format", "fmt", default="table", help="Output format (table/json)")
@click.option("--severity", help="Filter by severity")
def errors(fmt, severity):
    """Show detected errors.

    Displays all detected errors from the last scan. Results can be
    filtered by severity and exported to JSON format.

    \b
    OPTIONS:
      --format FMT       Output format: table or json (default: table)
      --severity SEV     Filter by severity level (error/warning/info)

    \b
    EXAMPLES:
      loki errors                          Show all errors in table
      loki errors --format json            Export as JSON
      loki errors --severity error         Show only errors
      loki errors --severity warning       Show only warnings

    \b
    NOTES:
      - Requires running `loki init` first
      - Table format is best for terminal viewing
      - JSON format is useful for scripting and CI/CD
    """
    from loki.commands.errors_cmd import execute_errors
    execute_errors(fmt, severity)


@main.command(short_help="Open web UI")
@click.option("--port", default=8080, help="Port for web UI")
def show(port):
    """Open web UI.

    Starts a local web server and opens the Loki dashboard in your
    browser. The dashboard provides real-time monitoring and visualization
    of your codebase errors.

    \b
    OPTIONS:
      --port PORT    Port number for web server (default: 8080)

    \b
    EXAMPLES:
      loki show                  Start web UI on port 8080
      loki show --port 3000      Start on custom port

    \b
    NOTES:
      - Requires running `loki init` first
      - Press Ctrl+C to stop the server
      - Dashboard shows real-time error updates
    """
    from loki.commands.show_cmd import execute_show
    execute_show(port)


@main.command(short_help="Describe errors in detail")
@click.option("--file", help="Describe errors in specific file")
def describe(file):
    """Describe errors in detail.

    Provides detailed explanations for detected errors, including
    root cause analysis, impact assessment, and recommended fixes.
    Uses AI to generate comprehensive error descriptions.

    \b
    OPTIONS:
      --file FILE    Focus on errors in a specific file

    \b
    EXAMPLES:
      loki describe                      Describe all errors
      loki describe --file app.py        Describe errors in app.py

    \b
    NOTES:
      - Requires running `loki init` first
      - AI features require API key (run `loki models`)
      - Detailed descriptions help understand complex errors
    """
    from loki.commands.describe_cmd import execute_describe
    execute_describe(file)


@main.command("ai", short_help="Chat with AI about your code")
@click.argument("question", required=False)
def ai_cmd(question):
    """Chat with AI about your code.

    Interactive AI chat session that answers questions about your
    codebase. Uses RAG (Retrieval-Augmented Generation) to provide
    context-aware responses based on your actual code.

    \b
    OPTIONS:
      QUESTION    Ask a single question without entering interactive mode

    \b
    EXAMPLES:
      loki ai                              Start interactive chat
      loki ai "What does this function do?"    Ask a single question
      loki ai "How do I fix this error?"       Get fix suggestions

    \b
    NOTES:
      - Requires running `loki init` first
      - Requires API key (run `loki models` to configure)
      - Type /exit or /quit to exit interactive mode
      - AI has access to your codebase via RAG index
    """
    from loki.commands.ai_cmd import execute_ai
    execute_ai(question)


@main.command(name="exit", short_help="Clear project cache")
@click.option("--force", is_flag=True, help="Skip confirmation")
def exit_cmd(force):
    """Clear project cache.

    Removes the .loki cache directory and all stored scan results,
    errors, and RAG index. Use this to reset Loki or free disk space.

    \b
    OPTIONS:
      --force    Skip confirmation prompt

    \b
    EXAMPLES:
      loki exit                Clear cache with confirmation
      loki exit --force        Clear cache without confirmation

    \b
    NOTES:
      - You will need to run `loki init` again after clearing cache
      - This does not affect your source code
      - Useful when switching between projects
    """
    from loki.commands.exit_cmd import execute_exit
    execute_exit(force)


@main.command(short_help="AI-powered fix suggestions")
@click.option("--dry-run", is_flag=True, help="Show fixes without applying")
@click.option("--file", help="Fix specific file")
def fix(dry_run, file):
    """AI-powered fix suggestions.

    Analyzes detected errors and suggests AI-powered fixes. Can apply
    fixes automatically or show suggestions for manual review.

    \b
    OPTIONS:
      --dry-run    Show fixes without applying them
      --file FILE  Fix errors in a specific file only

    \b
    EXAMPLES:
      loki fix                        Show fix suggestions
      loki fix --dry-run              Preview fixes without applying
      loki fix --file app.py          Fix errors in specific file

    \b
    NOTES:
      - Requires running `loki init` first
      - Requires API key (run `loki models` to configure)
      - Use --dry-run first to review changes before applying
      - Backups are created before applying fixes
    """
    from loki.commands.fix_cmd import execute_fix
    execute_fix(dry_run, file)


@main.command(short_help="Watch files for changes")
@click.option("--interval", default=5, help="Re-scan interval (seconds)")
def watch(interval):
    """Watch files for changes.

    Monitors your project directory for file changes and automatically
    re-scans when modifications are detected. Provides real-time error
    detection as you code.

    \b
    OPTIONS:
      --interval SEC    Seconds between re-scans (default: 5)

    \b
    EXAMPLES:
      loki watch                   Watch with 5-second interval
      loki watch --interval 10     Watch with 10-second interval
      loki watch --interval 2      Fast updates every 2 seconds

    \b
    NOTES:
      - Requires running `loki init` first
      - Press Ctrl+C to stop watching
      - Lower intervals use more CPU resources
      - Great for development with live error feedback
    """
    from loki.commands.watch_cmd import execute_watch
    execute_watch(interval)


@main.command(short_help="Generate markdown report")
@click.option("--output", help="Output file path")
def report(output):
    """Generate markdown report.

    Creates a comprehensive markdown report of all detected errors,
    statistics, and recommendations. Useful for documentation, code
    reviews, and tracking progress over time.

    \b
    OPTIONS:
      --output FILE    Output file path (default: loki-report.md)

    \b
    EXAMPLES:
      loki report                      Generate default report
      loki report --output REPORT.md   Generate with custom name

    \b
    NOTES:
      - Requires running `loki init` first
      - Report includes error summary, details, and trends
      - Markdown format is easy to share and version control
    """
    from loki.commands.report_cmd import execute_report
    execute_report(output)


@main.command(short_help="Manage AI providers")
@click.option("--set", "set_provider", help="Set provider")
@click.option("--list", "list_providers", is_flag=True, help="List providers")
def models(set_provider, list_providers):
    """Manage AI providers.

    Configure AI providers for error analysis and chat features.
    Supports multiple providers including Groq, OpenAI, and Anthropic.

    \b
    OPTIONS:
      --set PROVIDER    Set the active AI provider
      --list            List all available providers

    \b
    EXAMPLES:
      loki models --list                  Show available providers
      loki models --set groq              Set provider to Groq
      loki models --set openai            Set provider to OpenAI

    \b
    NOTES:
      - API keys are stored securely in OS keychain
      - Default provider is Groq (free tier available)
      - You will be prompted for API key when setting a provider
    """
    from loki.commands.models_cmd import execute_models
    execute_models(set_provider, list_providers)


@main.command(short_help="Capture console errors from running processes")
@click.argument("command", required=False)
def capture(command):
    """Capture console errors from running processes.

    Monitors a running process and captures any errors or exceptions
    it outputs to the console. Useful for debugging runtime errors
    that static analysis might miss.

    \b
    OPTIONS:
      COMMAND    The command to run and monitor

    \b
    EXAMPLES:
      loki capture python app.py           Capture errors from Python script
      loki capture node server.js          Capture errors from Node.js
      loki capture pytest                  Capture test failures

    \b
    NOTES:
      - Requires running `loki init` first
      - Captured errors are added to the cache
      - Use `loki errors` to view captured errors
      - Press Ctrl+C to stop capturing
    """
    from loki.commands.capture_cmd import execute_capture
    execute_capture(command)


@main.command(short_help="Inject error capture hook into Python files")
@click.option("--path", default=".", help="Path to inject hook")
def inject(path):
    """Inject error capture hook into Python files.

    Automatically adds error capture hooks to Python files in your
    project. These hooks capture runtime errors and send them to
    Loki for analysis.

    \b
    OPTIONS:
      --path PATH    Path to inject hooks (default: current directory)

    \b
    EXAMPLES:
      loki inject                    Inject hooks in current directory
      loki inject --path ./src       Inject hooks in specific folder

    \b
    NOTES:
      - Requires running `loki init` first
      - Only modifies Python files
      - Creates backups before modifying files
      - Use `loki exit` to remove hooks
    """
    from loki.commands.inject_cmd import execute_inject
    execute_inject(path)
