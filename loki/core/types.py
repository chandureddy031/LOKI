"""Data structures for Loki."""

from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Language(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    C = "c"
    CPP = "cpp"
    JAVA = "java"
    RUBY = "ruby"
    PHP = "php"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    SCALA = "scala"
    ERLANG = "erlang"
    HASKELL = "haskell"
    LUA = "lua"
    R = "r"
    OBJECTIVE_C = "objective-c"
    OBJECTIVE_CPP = "objective-cpp"
    UNKNOWN = "unknown"


@dataclass
class FileMetadata:
    path: str
    hash: str
    size: int
    language: Language
    lines: int
    last_modified: float


@dataclass
class ScanResult:
    project_hash: str
    created_at: float
    files: list[FileMetadata]
    structure: dict


@dataclass
class Error:
    file: str
    line: int
    column: int
    severity: Severity
    code: str
    message: str
    source: str
    fixable: bool
    suggestion: str | None = None


@dataclass
class ErrorSummary:
    total: int
    errors: int
    warnings: int
    info: int


@dataclass
class CodeChunk:
    file_path: str
    start_line: int
    end_line: int
    content: str
    language: Language


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: float
    context: list[str] = field(default_factory=list)


@dataclass
class CommandResult:
    success: bool
    message: str
    data: dict | None = None
    error: str | None = None
