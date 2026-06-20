"""File scanning and AST parsing for ALL languages."""

import hashlib
import os
from pathlib import Path

from .types import FileMetadata, Language, ScanResult


class FileScanner:
    """Scans directory and parses files for any language."""

    EXTENSION_MAP = {
        ".py": Language.PYTHON,
        ".js": Language.JAVASCRIPT,
        ".jsx": Language.JAVASCRIPT,
        ".ts": Language.TYPESCRIPT,
        ".tsx": Language.TYPESCRIPT,
        ".go": Language.GO,
        ".rs": Language.RUST,
        ".c": Language.C,
        ".cpp": Language.CPP,
        ".cc": Language.CPP,
        ".h": Language.C,
        ".hpp": Language.CPP,
        ".java": Language.JAVA,
        ".rb": Language.RUBY,
        ".php": Language.PHP,
        ".swift": Language.SWIFT,
        ".kt": Language.KOTLIN,
        ".scala": Language.SCALA,
        ".ex": Language.ERLANG,
        ".exs": Language.ERLANG,
        ".erl": Language.ERLANG,
        ".hs": Language.HASKELL,
        ".lua": Language.LUA,
        ".r": Language.R,
        ".R": Language.R,
        ".m": Language.OBJECTIVE_C,
        ".mm": Language.OBJECTIVE_CPP,
    }

    ENTRY_POINTS = {
        "main.py", "app.py", "server.py", "manage.py", "wsgi.py", "asgi.py",
        "index.js", "server.js", "app.js", "main.js",
        "index.ts", "server.ts", "app.ts", "main.ts",
        "main.go", "cmd/main.go",
        "main.rs", "src/main.rs",
        "main.c", "main.cpp",
        "Main.java", "Application.java",
        "Gemfile", "Rakefile",
        "composer.json",
        "Cargo.toml", "go.mod", "package.json", "pom.xml", "build.gradle",
    }

    def __init__(self, root_dir: str, ignore_patterns: list[str]):
        self.root_dir = Path(root_dir).resolve()
        self.ignore_patterns = ignore_patterns

    def scan(self) -> ScanResult:
        """Scan all files and return result."""
        files = []
        directories = set()

        for file_path in self._walk_files():
            try:
                metadata = self._parse_file(file_path)
                files.append(metadata)
                directories.add(str(file_path.parent.relative_to(self.root_dir)))
            except (OSError, PermissionError):
                continue

        structure = {
            "directories": sorted(directories),
            "entry_points": self._find_entry_points(files),
            "languages": self._count_languages(files),
        }

        project_hash = self._compute_project_hash()

        return ScanResult(
            project_hash=project_hash,
            created_at=os.path.getmtime(str(self.root_dir)),
            files=files,
            structure=structure,
        )

    def _walk_files(self) -> list[Path]:
        """Walk directory and return matching files."""
        files = []

        for root, dirs, filenames in os.walk(self.root_dir):
            root_path = Path(root)

            dirs[:] = [
                d for d in dirs
                if not self._should_ignore(d)
            ]

            for filename in filenames:
                if self._should_ignore(filename):
                    continue

                file_path = root_path / filename
                suffix = file_path.suffix.lower()

                if suffix in self.EXTENSION_MAP or filename in self.ENTRY_POINTS:
                    files.append(file_path)

        return files

    def _should_ignore(self, name: str) -> bool:
        """Check if file/directory should be ignored."""
        import fnmatch
        return any(fnmatch.fnmatch(name, pattern) for pattern in self.ignore_patterns)

    def _parse_file(self, file_path: Path) -> FileMetadata:
        """Parse file and extract metadata."""
        stat = file_path.stat()
        language = self.EXTENSION_MAP.get(file_path.suffix.lower(), Language.UNKNOWN)

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.count("\n") + 1
            file_hash = hashlib.sha256(content.encode()).hexdigest()
        except (OSError, UnicodeDecodeError):
            lines = 0
            file_hash = ""

        return FileMetadata(
            path=str(file_path.relative_to(self.root_dir)),
            hash=file_hash,
            size=stat.st_size,
            language=language,
            lines=lines,
            last_modified=stat.st_mtime,
        )

    def _find_entry_points(self, files: list[FileMetadata]) -> list[str]:
        """Find likely entry points."""
        entry_points = []
        for f in files:
            name = Path(f.path).name.lower()
            if name in [ep.lower() for ep in self.ENTRY_POINTS]:
                entry_points.append(f.path)
        return entry_points

    def _count_languages(self, files: list[FileMetadata]) -> dict:
        """Count files by language."""
        counts = {}
        for f in files:
            lang = f.language.value if hasattr(f.language, 'value') else str(f.language)
            counts[lang] = counts.get(lang, 0) + 1
        return counts

    def _compute_project_hash(self) -> str:
        """Compute hash of project path."""
        return hashlib.sha256(str(self.root_dir).encode()).hexdigest()[:12]
