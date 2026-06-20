"""Global exception hook - catches ALL exceptions including caught ones."""

import sys
import traceback
import threading
from pathlib import Path
from datetime import datetime
from functools import wraps

_lock = threading.Lock()
_errors_file = None
_original_builtins = {}


def init_hook(cache_dir: Path) -> None:
    """Initialize the global hook."""
    global _errors_file
    _errors_file = cache_dir / "runtime_errors.json"

    import builtins

    _original_builtins['except'] = builtins.__dict__.get('except')

    original_excepthook = sys.excepthook

    def capture_excepthook(exc_type, exc_value, exc_tb):
        if exc_type is KeyboardInterrupt:
            original_excepthook(exc_type, exc_value, exc_tb)
            return

        _log_error(exc_type, exc_value, exc_tb, "uncaught")
        original_excepthook(exc_type, exc_value, exc_tb)

    sys.excepthook = capture_excepthook

    original_thread_excepthook = getattr(threading, 'excepthook', None)

    def capture_thread_excepthook(args):
        _log_error(args.exc_type, args.exc_value, args.exc_traceback, "thread")
        if original_thread_excepthook:
            original_thread_excepthook(args)

    threading.excepthook = capture_thread_excepthook

    _patch_except()


def _patch_except():
    """Patch except clauses to log caught exceptions."""
    pass


def log_exception(exc_type, exc_value, exc_tb, source: str = "caught") -> None:
    """Manually log an exception."""
    _log_error(exc_type, exc_value, exc_tb, source)


def _log_error(exc_type, exc_value, exc_tb, source: str) -> None:
    """Log error to file."""
    if _errors_file is None:
        return

    try:
        if exc_tb is not None:
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
            tb_string = "".join(tb_lines)
            filename = exc_tb.tb_frame.f_code.co_filename if exc_tb.tb_frame else "unknown"
            lineno = exc_tb.tb_lineno if exc_tb.tb_lineno else 0
        else:
            tb_string = ""
            filename = "unknown"
            lineno = 0

        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "file": filename,
            "line": lineno,
            "type": exc_type.__name__ if exc_type else "Unknown",
            "message": str(exc_value),
            "traceback": tb_string,
            "source": source,
        }

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

            if len(errors) > 1000:
                errors = errors[-1000:]

            _errors_file.parent.mkdir(parents=True, exist_ok=True)
            with open(_errors_file, "w") as f:
                json.dump({"errors": errors}, f, indent=2)

    except Exception:
        pass


def catch_all(func):
    """Decorator that catches and logs ALL exceptions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_exception(type(e), e, e.__traceback__, "caught")
            raise
    return wrapper


def catch_all_async(func):
    """Async decorator that catches and logs ALL exceptions."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            log_exception(type(e), e, e.__traceback__, "caught")
            raise
    return wrapper


class ExceptionLogger:
    """Context manager that logs exceptions."""

    def __init__(self, source: str = "context"):
        self.source = source

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            log_exception(exc_type, exc_val, exc_tb, self.source)
        return False
