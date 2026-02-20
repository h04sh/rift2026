"""
Git Agent – Node 4 of the LangGraph pipeline.

Responsibilities:
  • Create branch: TEAM_NAME_LEADER_NAME_AI_Fix (UPPERCASE, underscores)
  • Stage all changes
  • Commit with prefix "[AI-AGENT] Fix: <description>"
  • Push to origin
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.state import AgentState


def _run_git(args: list[str], cwd: str, env: dict | None = None) -> tuple[int, str, str]:
    """Run a git command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _build_branch_name(team_name: str, leader_name: str) -> str:
    """
    Format: TEAM_NAME_LEADER_NAME_AI_Fix
    - UPPERCASE
    - Spaces → underscores
    """
    team = team_name.upper().replace(" ", "_")
    leader = leader_name.upper().replace(" ", "_")
    return f"{team}_{leader}_AI_Fix"


def _build_commit_message(fixes: list) -> str:
    """Build a meaningful commit message summarizing all fixes."""
    if not fixes:
        return "[AI-AGENT] Fix: apply automated code quality improvements"

    fix_lines = []
    for fix in fixes[:5]:  # summarize up to 5 fixes inline
        bug_type = fix.get("bug_type", "BUG")
        file = fix.get("file", "unknown")
        line = fix.get("line", 0)
        desc = fix.get("fix_description", "fix applied")
        fix_lines.append(f"  - {bug_type} error in {file} line {line} → Fix: {desc}")

    summary = "\n".join(fix_lines)
    if len(fixes) > 5:
        summary += f"\n  - ... and {len(fixes) - 5} more fix(es)"

    return f"[AI-AGENT] Fix: {len(fixes)} automated fix(es) applied\n\n{summary}"


def git_agent(state: "AgentState") -> "AgentState":
    """LangGraph node: create branch, commit fixes, and push."""

    clone_path = state.get("clone_path", "")
    team_name = state.get("team_name", "RIFT_TEAM")
    leader_name = state.get("leader_name", "LEADER")
    github_token = state.get("github_token", "")
    repo_url = state.get("repo_url", "")
    fixes = state.get("fixes", [])
    timeline = list(state.get("cicd_timeline", []))

    if not clone_path or state.get("status") == "failed":
        return state

    branch_name = _build_branch_name(team_name, leader_name)
    commit_message = _build_commit_message(fixes)

    timeline.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "git_started",
            "detail": f"Creating branch: {branch_name}",
            "status": "running",
        }
    )

    try:
        # Configure git identity
        _run_git(["config", "user.email", "ai-agent@rift2026.dev"], clone_path)
        _run_git(["config", "user.name", "RIFT AI Agent"], clone_path)

        # Create or reset branch
        rc, _, _ = _run_git(["checkout", "-b", branch_name], clone_path)
        if rc != 0:
            # Branch exists – reset it
            _run_git(["checkout", branch_name], clone_path)
            _run_git(["reset", "--hard", "HEAD"], clone_path)

        # Stage all changes
        _run_git(["add", "-A"], clone_path)

        # Check if there's anything to commit
        rc, status_out, _ = _run_git(["status", "--porcelain"], clone_path)
        if not status_out.strip():
            timeline.append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "git_nothing_to_commit",
                    "detail": "No file changes to commit",
                    "status": "success",
                }
            )
            return {
                **state,
                "branch_name": branch_name,
                "commit_sha": "",
                "cicd_timeline": timeline,
            }

        # Commit
        rc, out, err = _run_git(["commit", "-m", commit_message], clone_path)
        if rc != 0:
            raise RuntimeError(f"git commit failed: {err}")

        # Get commit SHA
        _, commit_sha, _ = _run_git(["rev-parse", "HEAD"], clone_path)

        # Set up remote with token if provided
        if github_token and "github.com" in repo_url:
            authed_url = repo_url.replace("https://", f"https://{github_token}@")
            _run_git(["remote", "set-url", "origin", authed_url], clone_path)

        # Push
        rc, _, err = _run_git(
            ["push", "--force-with-lease", "origin", branch_name],
            clone_path,
        )
        if rc != 0:
            # Try regular push if force-with-lease fails
            rc, _, err = _run_git(["push", "-u", "origin", branch_name], clone_path)
            if rc != 0:
                raise RuntimeError(f"git push failed: {err}")

        timeline.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "git_pushed",
                "detail": f"Pushed {len(fixes)} fix(es) to branch {branch_name} (SHA: {commit_sha[:7]})",
                "status": "success",
            }
        )

        return {
            **state,
            "branch_name": branch_name,
            "commit_sha": commit_sha,
            "cicd_timeline": timeline,
        }

    except Exception as exc:
        timeline.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "git_failed",
                "detail": str(exc),
                "status": "failure",
            }
        )
        return {
            **state,
            "branch_name": branch_name,
            "commit_sha": "",
            "cicd_timeline": timeline,
            "error_message": str(exc),
        }
