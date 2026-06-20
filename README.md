# loki-cli

AI-powered code analysis CLI with error detection, RAG chat, and web UI.

## Features

- **10 CLI commands** for code analysis
- **AI-powered** error detection and fixes
- **RAG chat** with your codebase
- **Web UI** with real-time monitoring
- **Secure** - API keys in OS keychain, encrypted cache

## Installation

```bash
pip install loki-cli
```

## Quick Start

```bash
loki init          # Scan codebase
loki errors        # Show errors
loki ai            # Chat with AI
loki show          # Open web UI
loki report        # Generate report
```

## Commands

| Command | Description |
|---------|-------------|
| `loki init` | Scan codebase, build cache |
| `loki errors` | Show detected errors |
| `loki show` | Open web UI |
| `loki describe` | Detailed error explanations |
| `loki ai` | Terminal chat with AI |
| `loki exit` | Clear cache |
| `loki fix` | AI-powered fix suggestions |
| `loki watch` | Live file monitoring |
| `loki report` | Generate markdown report |
| `loki models` | Switch AI providers |

## Security

- API keys stored in OS keychain (never in files)
- Cache encrypted with Fernet
- AI guardrails prevent prompt injection
- Secure deletion with 3-pass overwrite

## License

MIT
