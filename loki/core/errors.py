"""Error detection for ALL languages."""

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from .types import Error, ErrorSummary, Language, ScanResult, Severity


class ErrorDetector:
    """Detects errors for any language using multiple tools."""

    def __init__(self, scan_result: ScanResult, root_dir: str):
        self.scan_result = scan_result
        self.root_dir = Path(root_dir)
        self.errors: list[Error] = []

    def detect_all(self) -> list[Error]:
        """Run all detectors and merge results."""
        self.errors = []

        self.detect_syntax_errors()
        self.detect_language_linters()
        self.detect_compiler_errors()

        return self.errors

    def detect_syntax_errors(self) -> list[Error]:
        """Detect syntax errors via AST parsing."""
        for file_meta in self.scan_result.files:
            lang = file_meta.language
            file_path = self.root_dir / file_meta.path

            if lang == Language.PYTHON:
                self._check_python_syntax(file_meta, file_path)
            elif lang in (Language.JAVASCRIPT, Language.TYPESCRIPT):
                self._check_js_syntax(file_meta, file_path)
            elif lang == Language.GO:
                self._check_go_syntax(file_meta, file_path)
            elif lang == Language.RUST:
                self._check_rust_syntax(file_meta, file_path)
            elif lang in (Language.C, Language.CPP):
                self._check_c_syntax(file_meta, file_path)
            elif lang == Language.JAVA:
                self._check_java_syntax(file_meta, file_path)

        return self.errors

    def _check_python_syntax(self, file_meta, file_path: Path):
        """Check Python syntax."""
        try:
            content = file_path.read_text(encoding="utf-8")
            ast.parse(content, filename=file_meta.path)
        except SyntaxError as e:
            self.errors.append(Error(
                file=file_meta.path,
                line=e.lineno or 0,
                column=e.offset or 0,
                severity=Severity.ERROR,
                code="E0001",
                message=str(e.msg),
                source="python_ast",
                fixable=True,
            ))
        except (UnicodeDecodeError, OSError):
            pass

    def _check_js_syntax(self, file_meta, file_path: Path):
        """Check JavaScript/TypeScript syntax."""
        try:
            result = subprocess.run(
                ["node", "--check", str(file_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                error_msg = result.stderr.strip().split("\n")[0] if result.stderr else "Syntax error"
                line = 0
                match = re.search(r":(\d+)", result.stderr)
                if match:
                    line = int(match.group(1))

                self.errors.append(Error(
                    file=file_meta.path,
                    line=line,
                    column=0,
                    severity=Severity.ERROR,
                    code="JS001",
                    message=error_msg,
                    source="node_syntax",
                    fixable=True,
                ))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    def _check_go_syntax(self, file_meta, file_path: Path):
        """Check Go syntax."""
        try:
            result = subprocess.run(
                ["go", "vet", str(file_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                for line in result.stdout.split("\n") + result.stderr.split("\n"):
                    if line.strip():
                        self.errors.append(Error(
                            file=file_meta.path,
                            line=0,
                            column=0,
                            severity=Severity.ERROR,
                            code="GO001",
                            message=line.strip(),
                            source="go_vet",
                            fixable=True,
                        ))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    def _check_rust_syntax(self, file_meta, file_path: Path):
        """Check Rust syntax."""
        try:
            result = subprocess.run(
                ["rustc", "--edition", "2021", "--crate-type", "lib", str(file_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                for line in result.stderr.split("\n"):
                    if "error" in line.lower():
                        self.errors.append(Error(
                            file=file_meta.path,
                            line=0,
                            column=0,
                            severity=Severity.ERROR,
                            code="RS001",
                            message=line.strip(),
                            source="rustc",
                            fixable=True,
                        ))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    def _check_c_syntax(self, file_meta, file_path: Path):
        """Check C/C++ syntax."""
        try:
            compiler = "gcc" if file_meta.language == Language.C else "g++"
            result = subprocess.run(
                [compiler, "-fsyntax-only", str(file_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                for line in result.stderr.split("\n"):
                    if "error:" in line.lower():
                        self.errors.append(Error(
                            file=file_meta.path,
                            line=0,
                            column=0,
                            severity=Severity.ERROR,
                            code="C001",
                            message=line.strip(),
                            source="gcc",
                            fixable=True,
                        ))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    def _check_java_syntax(self, file_meta, file_path: Path):
        """Check Java syntax."""
        try:
            result = subprocess.run(
                ["javac", "-version", str(file_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                for line in result.stderr.split("\n"):
                    if "error" in line.lower():
                        self.errors.append(Error(
                            file=file_meta.path,
                            line=0,
                            column=0,
                            severity=Severity.ERROR,
                            code="JAVA001",
                            message=line.strip(),
                            source="javac",
                            fixable=True,
                        ))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    def detect_language_linters(self) -> list[Error]:
        """Run language-specific linters."""
        self._run_pylint()
        self._run_mypy()
        self._run_eslint()
        self._run_flake8()

        return self.errors

    def _run_pylint(self):
        """Run pylint on Python files."""
        python_files = [
            str(self.root_dir / f.path)
            for f in self.scan_result.files
            if f.language == Language.PYTHON
        ]

        if not python_files:
            return

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pylint", "--output-format=json", "--disable=C,R"] + python_files[:5],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.stdout:
                pylint_errors = json.loads(result.stdout)
                for e in pylint_errors:
                    self.errors.append(Error(
                        file=e.get("path", ""),
                        line=e.get("line", 0),
                        column=e.get("column", 0),
                        severity=self._map_pylint_type(e.get("type", "")),
                        code=e.get("message-id", ""),
                        message=e.get("message", ""),
                        source="pylint",
                        fixable=True,
                    ))
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass

    def _run_mypy(self):
        """Run mypy on Python files."""
        python_files = [
            str(self.root_dir / f.path)
            for f in self.scan_result.files
            if f.language == Language.PYTHON
        ]

        if not python_files:
            return

        try:
            result = subprocess.run(
                [sys.executable, "-m", "mypy", "--output-json"] + python_files[:5],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.stdout:
                mypy_data = json.loads(result.stdout)
                for e in mypy_data.get("errors", []):
                    self.errors.append(Error(
                        file=e.get("file", ""),
                        line=e.get("line", 0),
                        column=e.get("column", 0),
                        severity=Severity.ERROR if e.get("severity") == "error" else Severity.WARNING,
                        code=e.get("code", ""),
                        message=e.get("message", ""),
                        source="mypy",
                        fixable=True,
                    ))
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, KeyError):
            pass

    def _run_eslint(self):
        """Run ESLint on JS/TS files."""
        js_files = [
            str(self.root_dir / f.path)
            for f in self.scan_result.files
            if f.language in (Language.JAVASCRIPT, Language.TYPESCRIPT)
        ]

        if not js_files:
            return

        try:
            result = subprocess.run(
                ["npx", "eslint", "--format=json"] + js_files[:5],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.stdout:
                eslint_errors = json.loads(result.stdout)
                for file_result in eslint_errors:
                    for msg in file_result.get("messages", []):
                        self.errors.append(Error(
                            file=file_result.get("filePath", ""),
                            line=msg.get("line", 0),
                            column=msg.get("column", 0),
                            severity=Severity.ERROR if msg.get("severity") == 2 else Severity.WARNING,
                            code=msg.get("ruleId", ""),
                            message=msg.get("message", ""),
                            source="eslint",
                            fixable=bool(msg.get("fix")),
                        ))
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass

    def _run_flake8(self):
        """Run flake8 on Python files."""
        python_files = [
            str(self.root_dir / f.path)
            for f in self.scan_result.files
            if f.language == Language.PYTHON
        ]

        if not python_files:
            return

        try:
            result = subprocess.run(
                [sys.executable, "-m", "flake8", "--format=json"] + python_files[:5],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.stdout:
                flake8_errors = json.loads(result.stdout)
                for file_path, issues in flake8_errors.items():
                    for issue in issues:
                        self.errors.append(Error(
                            file=file_path,
                            line=issue.get("line", 0),
                            column=issue.get("column", 0),
                            severity=Severity.WARNING,
                            code=issue.get("code", ""),
                            message=issue.get("text", ""),
                            source="flake8",
                            fixable=True,
                        ))
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass

    def detect_compiler_errors(self) -> list[Error]:
        """Detect errors from build/compile output."""
        build_files = ["Makefile", "CMakeLists.txt", "build.gradle", "pom.xml"]
        for build_file in build_files:
            if (self.root_dir / build_file).exists():
                self._run_make(build_file)
                break

        return self.errors

    def _run_make(self, build_file: str):
        """Run make and capture errors."""
        try:
            result = subprocess.run(
                ["make", "-n"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(self.root_dir),
            )

            if result.returncode != 0:
                for line in result.stderr.split("\n"):
                    if "error" in line.lower():
                        self.errors.append(Error(
                            file="",
                            line=0,
                            column=0,
                            severity=Severity.ERROR,
                            code="BUILD001",
                            message=line.strip(),
                            source="make",
                            fixable=False,
                        ))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    def _map_pylint_type(self, msg_type: str) -> Severity:
        """Map pylint message type to severity."""
        mapping = {
            "error": Severity.ERROR,
            "warning": Severity.WARNING,
            "convention": Severity.INFO,
            "refactor": Severity.INFO,
            "fatal": Severity.ERROR,
        }
        return mapping.get(msg_type, Severity.INFO)

    def get_summary(self) -> ErrorSummary:
        """Get error count by severity."""
        errors = sum(1 for e in self.errors if e.severity == Severity.ERROR)
        warnings = sum(1 for e in self.errors if e.severity == Severity.WARNING)
        info = sum(1 for e in self.errors if e.severity == Severity.INFO)

        return ErrorSummary(
            total=len(self.errors),
            errors=errors,
            warnings=warnings,
            info=info,
        )
