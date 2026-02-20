"""
Results serialiser – writes the final AgentState to results.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.state import AgentState

RESULTS_PATH = Path(__file__).parent / "results.json"


def _format_fixes_output(fixes: list) -> list[str]:
    """
    Format fixes in EXACT required output format:
    "LINTING error in src/utils.py line 15 → Fix: remove the import statement"
    """
    output_lines = []
    for fix in fixes:
        bug_type = fix.get("bug_type", "BUG")
        file = fix.get("file", "unknown")
        line = fix.get("line", 0)
        desc = fix.get("fix_description", "fix applied")
        output_lines.append(
            f"{bug_type} error in {file} line {line} → Fix: {desc}"
        )
    return output_lines


def write_results(state: "AgentState") -> None:
    """Serialise AgentState to results.json."""

    # Build the formatted test-case output list
    fixes_formatted = _format_fixes_output(state.get("fixes", []))

    payload = {
        "run_id": state.get("run_id", ""),
        "repo_url": state.get("repo_url", ""),
        "team_name": state.get("team_name", ""),
        "leader_name": state.get("leader_name", ""),
        "branch_name": state.get("branch_name", ""),
        "commit_sha": state.get("commit_sha", ""),
        "pr_url": state.get("pr_url", ""),
        "language": state.get("language", "python"),
        "status": state.get("status", "unknown"),
        "started_at": state.get("started_at", ""),
        "finished_at": state.get("finished_at", ""),
        "duration_seconds": state.get("duration_seconds", 0),
        "retry_count": state.get("retry_count", 0),
        "retry_limit": state.get("retry_limit", 5),
        "test_summary": {
            "total_tests": state.get("total_tests", 0),
            "tests_passed": state.get("tests_passed", 0),
            "tests_failed": state.get("tests_failed", 0),
        },
        "failures": state.get("failures", []),
        "fixes": state.get("fixes", []),
        "fixes_formatted_output": fixes_formatted,
        "score": state.get("score", {}),
        "cicd_timeline": state.get("cicd_timeline", []),
        "cicd_status": state.get("cicd_status", "pending"),
        "error_message": state.get("error_message"),
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
