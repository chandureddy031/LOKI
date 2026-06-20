"""loki models command."""

from rich.console import Console
from rich.table import Table

from ..core.config import ConfigManager
from ..security.secret_manager import SecretManager, SecurityError


console = Console()

PROVIDERS = {
    "groq": {"name": "Groq", "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]},
    "openai": {"name": "OpenAI", "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]},
    "anthropic": {"name": "Anthropic", "models": ["claude-3-sonnet-20240229", "claude-3-haiku-20240307"]},
    "openrouter": {"name": "OpenRouter", "models": ["openai/gpt-4", "anthropic/claude-3-sonnet"]},
}


def execute_models(set_provider: str = None, list_providers: bool = False) -> None:
    """Manage AI providers."""
    config = ConfigManager()
    secret_manager = SecretManager()

    if list_providers:
        table = Table(title="Available Providers")
        table.add_column("Provider")
        table.add_column("Models")
        table.add_column("Status")

        for key, info in PROVIDERS.items():
            has_key = secret_manager.retrieve_key(key) is not None
            status = "[green]Configured[/green]" if has_key else "[red]Not configured[/red]"
            table.add_row(info["name"], ", ".join(info["models"]), status)

        console.print(table)
        return

    if set_provider:
        if set_provider not in PROVIDERS:
            console.print(f"[red]Unknown provider: {set_provider}[/red]")
            console.print(f"Available: {', '.join(PROVIDERS.keys())}")
            return

        config.set_provider(set_provider)
        console.print(f"[green]Provider set to {PROVIDERS[set_provider]['name']}[/green]")

        api_key = secret_manager.retrieve_key(set_provider)
        if not api_key:
            console.print(f"\n[yellow]No API key found for {PROVIDERS[set_provider]['name']}.[/yellow]")
            console.print("Please enter your API key:")
            try:
                key = input("> ").strip()
                if key:
                    secret_manager.store_key(set_provider, key)
                    console.print("[green]API key saved securely.[/green]")
            except SecurityError as e:
                console.print(f"[red]Error: {e}[/red]")

        models = PROVIDERS[set_provider]["models"]
        console.print(f"\nAvailable models: {', '.join(models)}")
        console.print("To change model, edit ~/.loki/config.json")
        return

    current = config.get_provider()
    console.print(f"Current provider: [bold]{PROVIDERS.get(current, {}).get('name', current)}[/bold]")
    console.print(f"Current model: [bold]{config.get_model()}[/bold]")
    console.print("\nUse `loki models --set <provider>` to change.")
    console.print("Use `loki models --list` to see all providers.")
