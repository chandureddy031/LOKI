"""Runtime error capture."""

import sys
import traceback
import threading
from pathlib import Path
from datetime import datetime

_lock = threading.Lock()
_errors_file = None


def setup_runtime_capture(cache_dir: Path) -> None:
    """Setup global exception hook to capture runtime errors."""
    global _errors_file

    _errors_file = cache_dir / "runtime_errors.json"

    original_excepthook = sys.excepthook

    def capture_excepthook(exc_type, exc_value, exc_tb):
        if exc_type is KeyboardInterrupt:
            original_excepthook(exc_type, exc_value, exc_tb)
            return

        try:
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
            tb_string = "".join(tb_lines)

            frame = exc_tb.tb_lineno
            filename = exc_tb.tb_frame.f_code.co_filename if exc_tb.tb_frame else "unknown"

            error_entry = {
                "timestamp": datetime.now().isoformat(),
                "file": filename,
                "line": exc_tb.tb_lineno if exc_tb.tb_lineno else 0,
                "type": exc_type.__name__ if exc_type else "Unknown",
                "message": str(exc_value),
                "traceback": tb_string,
                "source": "runtime",
            }

            _save_runtime_error(error_entry)

        except Exception:
            pass

        original_excepthook(exc_type, exc_value, exc_tb)

    sys.excepthook = capture_excepthook

    original_thread_excepthook = threading.excepthook if hasattr(threading, 'excepthook') else None

    def capture_thread_excepthook(args):
        try:
            exc_type = args.exc_type
            exc_value = args.exc_value
            exc_traceback = args.exc_traceback

            tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            tb_string = "".join(tb_lines)

            error_entry = {
                "timestamp": datetime.now().isoformat(),
                "file": args.thread.name if hasattr(args, 'thread') else "thread",
                "line": 0,
                "type": exc_type.__name__ if exc_type else "ThreadError",
                "message": str(exc_value),
                "traceback": tb_string,
                "source": "runtime_thread",
            }

            _save_runtime_error(error_entry)

        except Exception:
            pass

    threading.excepthook = capture_thread_excepthook


def capture_console_error(message: str, level: str = "error") -> None:
    """Capture a console/log error."""
    error_entry = {
        "timestamp": datetime.now().isoformat(),
        "file": "",
        "line": 0,
        "type": level.upper(),
        "message": message,
        "traceback": "",
        "source": "console",
    }
    _save_runtime_error(error_entry)


def capture_exception(exc_type, exc_value, exc_tb, context: str = "") -> None:
    """Manually capture an exception."""
    try:
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        tb_string = "".join(tb_lines)

        filename = exc_tb.tb_frame.f_code.co_filename if exc_tb and exc_tb.tb_frame else "unknown"

        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "file": filename,
            "line": exc_tb.tb_lineno if exc_tb else 0,
            "type": exc_type.__name__ if exc_type else "Unknown",
            "message": str(exc_value),
            "traceback": tb_string,
            "source": "runtime",
        }

        _save_runtime_error(error_entry)
    except Exception:
        pass


def get_runtime_errors() -> list[dict]:
    """Get all captured runtime errors."""
    if _errors_file is None or not _errors_file.exists():
        return []

    import json
    try:
        with open(_errors_file) as f:
            data = json.load(f)
            return data.get("errors", [])
    except (json.JSONDecodeError, OSError):
        return []


def clear_runtime_errors() -> None:
    """Clear runtime errors."""
    if _errors_file and _errors_file.exists():
        import json
        with open(_errors_file, "w") as f:
            json.dump({"errors": []}, f)


def _save_runtime_error(error_entry: dict) -> None:
    """Save error to file."""
    if _errors_file is None:
        return

    with _lock:
        import json

        errors = []
        if _errors_file.exists():
            try:
                with open(_errors_file) as f:
                    data = json.load(f)
                    errors = data.get("errors", [])
            except (json.JSONDecodeError, OSError):
                errors = []

        errors.append(error_entry)

        if len(errors) > 500:
            errors = errors[-500:]

        _errors_file.parent.mkdir(parents=True, exist_ok=True)
        with open(_errors_file, "w") as f:
            json.dump({"errors": errors}, f, indent=2)
