"""
Clone Agent – Node 1 of the LangGraph pipeline.

Responsibilities:
  • Accept a GitHub repo URL
  • Clone it into a temporary directory
  • Detect the primary language (Python / JavaScript / TypeScript)
  • Return updated state
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.state import AgentState


# ---------------------------------------------------------------------------
# Language detection helpers
# ---------------------------------------------------------------------------

def _detect_language(repo_path: str) -> str:
    root = Path(repo_path)
    counts: dict[str, int] = {"python": 0, "typescript": 0, "javascript": 0}

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix == ".py":
            counts["python"] += 1
        elif p.suffix == ".ts" or p.suffix == ".tsx":
            counts["typescript"] += 1
        elif p.suffix in (".js", ".jsx"):
            counts["javascript"] += 1

    # Typescript takes precedence over plain JS
    if counts["typescript"] > 0 and counts["typescript"] >= counts["javascript"]:
        return "typescript"
    if counts["python"] >= counts["javascript"] and counts["python"] >= counts["typescript"]:
        return "python" if counts["python"] > 0 else "javascript"
    return "javascript"


# ---------------------------------------------------------------------------
# Node entry point
# ---------------------------------------------------------------------------

def clone_agent(state: "AgentState") -> "AgentState":
    """LangGraph node: clone the repository and detect its language."""

    repo_url = state["repo_url"]
    github_token = state.get("github_token", "")
    timeline = list(state.get("cicd_timeline", []))

    # Inject token into URL for private repos
    if github_token and "github.com" in repo_url:
        repo_url = repo_url.replace(
            "https://",
            f"https://{github_token}@",
        )

    # Remove any existing clone for idempotency
    clone_path = state.get("clone_path", "")
    if clone_path and Path(clone_path).exists():
        shutil.rmtree(clone_path, ignore_errors=True)

    # Create a unique directory name but don't create it yet (git clone will create it)
    tmp_base = tempfile.gettempdir()
    tmp_dir = os.path.join(tmp_base, f"rift_agent_{int(time.time())}_{os.getpid()}")

    timeline.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "clone_started",
            "detail": f"Cloning {state['repo_url']} into {tmp_dir}",
            "status": "running",
        }
    )

    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, tmp_dir],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=tmp_base,  # Set working directory to temp folder
        )

        if result.returncode != 0:
            error_msg = f"git clone failed (exit code {result.returncode}): {result.stderr.strip()}"
            if result.stdout:
                error_msg += f"\nStdout: {result.stdout.strip()}"
            raise RuntimeError(error_msg)

        # Verify the clone was successful
        if not Path(tmp_dir).exists():
            raise RuntimeError(f"Clone directory {tmp_dir} was not created")

        language = _detect_language(tmp_dir)

        timeline.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "clone_success",
                "detail": f"Repository cloned. Detected language: {language}",
                "status": "success",
            }
        )

        return {
            **state,
            "clone_path": tmp_dir,
            "language": language,
            "cicd_timeline": timeline,
            "error_message": None,
        }

    except Exception as exc:
        # Clean up on failure
        if Path(tmp_dir).exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)
        timeline.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "clone_failed",
                "detail": str(exc),
                "status": "failure",
            }
        )
        return {
            **state,
            "clone_path": "",
            "language": "unknown",
            "cicd_timeline": timeline,
            "status": "failed",
            "error_message": str(exc),
        }
