"""
Analyze Agent – Node 2 of the LangGraph pipeline.

Responsibilities:
  • Discover test files
  • Run the appropriate test runner (pytest / jest / eslint)
  • Parse failures into structured FailureEvent objects
  • Update state with failure list
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from agent.state import AgentState, FailureEvent

ALLOWED_BUG_TYPES = {"LINTING", "SYNTAX", "LOGIC", "TYPE_ERROR", "IMPORT", "INDENTATION"}

# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def _parse_pytest_output(output: str, root: str) -> List["FailureEvent"]:
    """
    Parse pytest's verbose / short test summary output.
    Extracts: file, line, error category.
    """
    failures: List[FailureEvent] = []

    # Pattern 1: "FAILED src/utils.py::test_foo - AssertionError"
    # Pattern 2: "src/utils.py:15: SyntaxError: ..."
    error_pattern = re.compile(
        r"(?P<file>[^\s:]+\.py):(?P<line>\d+):\s*(?P<etype>[A-Za-z]+Error|SyntaxError|IndentationError|ImportError|TypeError):\s*(?P<msg>.+)"
    )
    # ESLint / pylint style: "src/utils.py:15:4: E302 ..."
    lint_pattern = re.compile(
        r"(?P<file>[^\s:]+\.py):(?P<line>\d+):\d+:\s*(?P<code>[A-Z]\d+)\s+(?P<msg>.+)"
    )

    for line in output.splitlines():
        m = error_pattern.search(line)
        if m:
            etype = m.group("etype").upper()
            bug_type = _classify_python_error(etype)
            failures.append(
                {
                    "bug_type": bug_type,
                    "file": m.group("file"),
                    "line": int(m.group("line")),
                    "message": m.group("msg").strip(),
                }
            )
            continue

        m = lint_pattern.search(line)
        if m:
            failures.append(
                {
                    "bug_type": "LINTING",
                    "file": m.group("file"),
                    "line": int(m.group("line")),
                    "message": f"{m.group('code')} {m.group('msg').strip()}",
                }
            )

    return failures


def _classify_python_error(etype: str) -> str:
    mapping = {
        "SYNTAXERROR": "SYNTAX",
        "INDENTATIONERROR": "INDENTATION",
        "IMPORTERROR": "IMPORT",
        "MODULENOTFOUNDERROR": "IMPORT",
        "TYPEERROR": "TYPE_ERROR",
        "NAMEERROR": "LOGIC",
        "ATTRIBUTEERROR": "LOGIC",
    }
    return mapping.get(etype.upper(), "LOGIC")


def _parse_jest_output(output: str) -> List["FailureEvent"]:
    """Parse Jest/ESLint JSON or text output."""
    failures: List[FailureEvent] = []

    # Pattern: "● src/utils.js › test description\n  TypeError: ..."
    block_pattern = re.compile(
        r"●\s+(?P<suite>.+?)\n.+?(?P<etype>TypeError|SyntaxError|ReferenceError|Error):\s+(?P<msg>.+)",
        re.MULTILINE | re.DOTALL,
    )
    line_pattern = re.compile(r"at .+\((?P<file>[^:)]+):(?P<line>\d+):")

    for block in block_pattern.finditer(output):
        etype = block.group("etype")
        msg = block.group("msg").strip()
        # try to find file/line in block
        lm = line_pattern.search(block.group(0))
        file_n = lm.group("file") if lm else "unknown"
        line_n = int(lm.group("line")) if lm else 0
        failures.append(
            {
                "bug_type": _classify_js_error(etype),
                "file": file_n,
                "line": line_n,
                "message": msg,
            }
        )

    return failures


def _classify_js_error(etype: str) -> str:
    mapping = {
        "TypeError": "TYPE_ERROR",
        "SyntaxError": "SYNTAX",
        "ReferenceError": "IMPORT",
    }
    return mapping.get(etype, "LOGIC")


def _run_eslint(clone_path: str) -> List["FailureEvent"]:
    """Run ESLint and parse results."""
    failures: List[FailureEvent] = []
    try:
        r = subprocess.run(
            ["npx", "eslint", ".", "--format", "compact", "--no-eslintrc", "-c",
             '{"rules":{"no-undef":"error","no-unused-vars":"warn"}}'],
            cwd=clone_path,
            capture_output=True,
            text=True,
            timeout=60,
            shell=True,  # Use shell on Windows
        )
        # compact: path/file.js: line 10, col 5, Error - message (rule)
        pattern = re.compile(
            r"(?P<file>[^:]+):\s+line (?P<line>\d+),\s+col \d+,\s+(?:Error|Warning)\s+-\s+(?P<msg>.+?)(?:\s+\(.+\))?$"
        )
        for line in r.stdout.splitlines():
            m = pattern.match(line.strip())
            if m:
                failures.append(
                    {
                        "bug_type": "LINTING",
                        "file": m.group("file").strip(),
                        "line": int(m.group("line")),
                        "message": m.group("msg").strip(),
                    }
                )
    except Exception:
        pass
    return failures


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def _count_tests_in_output(output: str, language: str) -> tuple[int, int]:
    """Return (total, passed) from test runner output."""
    if language == "python":
        # "5 passed, 2 failed"
        m = re.search(r"(\d+) passed", output)
        f = re.search(r"(\d+) failed", output)
        passed = int(m.group(1)) if m else 0
        failed = int(f.group(1)) if f else 0
        return passed + failed, passed
    else:
        # Jest: "Tests: 2 failed, 5 passed, 7 total"
        m = re.search(r"Tests:\s+(?:(\d+) failed,\s+)?(\d+) passed(?:,\s+(\d+) total)?", output)
        if m:
            failed = int(m.group(1) or 0)
            passed = int(m.group(2) or 0)
            total = int(m.group(3) or (passed + failed))
            return total, passed
    return 0, 0


def analyze_agent(state: "AgentState") -> "AgentState":
    """LangGraph node: run tests and collect failures."""

    clone_path = state.get("clone_path", "")
    language = state.get("language", "python")
    timeline = list(state.get("cicd_timeline", []))

    if not clone_path or state.get("status") == "failed":
        return state

    timeline.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "analysis_started",
            "detail": f"Running {language} tests in {clone_path}",
            "status": "running",
        }
    )

    failures: List[FailureEvent] = []
    raw_output = ""
    total_tests = 0
    tests_passed = 0

    try:
        if language == "python":
            # Try pytest first
            result = subprocess.run(
                ["python", "-m", "pytest", "--tb=short", "-v", clone_path],
                capture_output=True,
                text=True,
                timeout=180,
                cwd=clone_path,
            )
            raw_output = result.stdout + result.stderr
            failures = _parse_pytest_output(raw_output, clone_path)
            total_tests, tests_passed = _count_tests_in_output(raw_output, language)

            # Also run flake8 for linting
            try:
                lint_result = subprocess.run(
                    ["python", "-m", "flake8", ".", "--max-line-length=120",
                     "--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=clone_path,
                )
                lint_output = lint_result.stdout
                lint_pattern = re.compile(
                    r"(?P<file>[^:]+):(?P<line>\d+):\d+:\s*(?P<code>[EWF]\d+)\s+(?P<msg>.+)"
                )
                for line in lint_output.splitlines():
                    m = lint_pattern.match(line)
                    if m:
                        failures.append(
                            {
                                "bug_type": "LINTING",
                                "file": m.group("file"),
                                "line": int(m.group("line")),
                                "message": f"{m.group('code')} {m.group('msg').strip()}",
                            }
                        )
            except Exception:
                pass

        else:
            # JavaScript / TypeScript
            # Check if package.json exists and has test script
            package_json = Path(clone_path) / "package.json"
            has_tests = False
            
            if package_json.exists():
                import json
                try:
                    with open(package_json, 'r', encoding='utf-8') as f:
                        pkg = json.load(f)
                        scripts = pkg.get('scripts', {})
                        has_tests = 'test' in scripts
                        
                        # Try to run npm test if available
                        if has_tests:
                            result = subprocess.run(
                                ["npm", "test", "--", "--no-coverage", "--forceExit", "--passWithNoTests"],
                                capture_output=True,
                                text=True,
                                timeout=60,  # Reduced timeout
                                cwd=clone_path,
                                shell=True,
                            )
                            raw_output = result.stdout + result.stderr
                        else:
                            # No test script, skip
                            raw_output = "No test script found in package.json"
                except Exception as e:
                    raw_output = f"Error reading package.json: {str(e)}"
            else:
                # No package.json, skip tests
                raw_output = "No package.json found - skipping JavaScript tests"
            
            failures = _parse_jest_output(raw_output) if has_tests else []
            total_tests, tests_passed = _count_tests_in_output(raw_output, language) if has_tests else (0, 0)
            
            # Only run eslint if we have a package.json
            if package_json.exists():
                failures += _run_eslint(clone_path)

        tests_failed = len([f for f in failures if f])

        # Deduplicate
        seen = set()
        deduped: List[FailureEvent] = []
        for f in failures:
            key = (f["bug_type"], f["file"], f["line"])
            if key not in seen:
                seen.add(key)
                deduped.append(f)
        failures = deduped

        timeline.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "analysis_complete",
                "detail": f"Found {len(failures)} failure(s). {tests_passed}/{total_tests} tests passed.",
                "status": "success" if len(failures) == 0 else "failure",
            }
        )

        return {
            **state,
            "failures": failures,
            "total_tests": total_tests,
            "tests_passed": tests_passed,
            "tests_failed": len(failures),
            "cicd_timeline": timeline,
        }

    except Exception as exc:
        error_detail = f"{type(exc).__name__}: {str(exc)}"
        if "WinError 2" in str(exc) or "cannot find" in str(exc).lower():
            error_detail += " - Test runner not found. For JavaScript projects, ensure npm/npx is installed and in PATH."
        
        timeline.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "analysis_error",
                "detail": error_detail,
                "status": "failure",
            }
        )
        return {
            **state,
            "failures": [],
            "total_tests": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "cicd_timeline": timeline,
            "error_message": error_detail,
        }
