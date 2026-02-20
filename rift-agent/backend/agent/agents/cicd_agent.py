"""
CI/CD Monitor Agent – Node 5 of the LangGraph pipeline.

Responsibilities:
  • Poll GitHub Actions API for the workflow run created by the push
  • Log status changes to cicd_timeline
  • Return final pass/fail status
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.state import AgentState


def cicd_agent(state: "AgentState") -> "AgentState":
    """LangGraph node: poll GitHub Actions and track CI/CD status."""

    github_token = state.get("github_token", "")
    repo_url = state.get("repo_url", "")
    branch_name = state.get("branch_name", "")
    commit_sha = state.get("commit_sha", "")
    timeline = list(state.get("cicd_timeline", []))

    if not github_token or not commit_sha:
        # No GitHub token/commit – simulate a local CI pass based on fix results
        fixes = state.get("fixes", [])
        applied = sum(1 for f in fixes if f.get("status") == "applied")
        ci_status = "success" if applied > 0 and len(state.get("failures", [])) > 0 else "failure"

        timeline.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "cicd_simulated",
                "detail": "No GitHub token provided – CI/CD result inferred from fix results",
                "status": ci_status,
            }
        )
        return {
            **state,
            "cicd_status": ci_status,
            "cicd_timeline": timeline,
        }

    # Parse owner/repo from URL
    import re
    m = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)", repo_url)
    if not m:
        timeline.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "cicd_skipped",
                "detail": "Cannot parse owner/repo from URL – skipping CI/CD polling",
                "status": "pending",
            }
        )
        return {**state, "cicd_status": "pending", "cicd_timeline": timeline}

    owner = m.group("owner")
    repo = m.group("repo")

    timeline.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "cicd_polling_started",
            "detail": f"Polling GitHub Actions for {owner}/{repo} on branch {branch_name}",
            "status": "running",
        }
    )

    try:
        from github_integration import get_latest_workflow_run, get_workflow_status

        # Wait briefly for GitHub to register the push
        time.sleep(5)

        run_id = get_latest_workflow_run(owner, repo, branch_name, github_token)
        if not run_id:
            timeline.append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "cicd_no_workflow",
                    "detail": "No workflow run found – repository may not have GitHub Actions configured",
                    "status": "pending",
                }
            )
            return {**state, "cicd_status": "pending", "cicd_timeline": timeline}

        # Poll until complete (max 10 min)
        max_polls = 60
        poll_interval = 10  # seconds
        last_status = ""

        for _ in range(max_polls):
            status, conclusion = get_workflow_status(owner, repo, run_id, github_token)

            if status != last_status:
                timeline.append(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "event": f"cicd_{status}",
                        "detail": f"Workflow run {run_id} – status: {status}"
                        + (f", conclusion: {conclusion}" if conclusion else ""),
                        "status": "running" if status in ("queued", "in_progress") else (
                            "success" if conclusion == "success" else "failure"
                        ),
                    }
                )
                last_status = status

            if status == "completed":
                final_status = "success" if conclusion == "success" else "failure"
                return {
                    **state,
                    "cicd_status": final_status,
                    "cicd_timeline": timeline,
                }

            time.sleep(poll_interval)

        # Timed out
        timeline.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "cicd_timeout",
                "detail": "Polling timed out after 10 minutes",
                "status": "failure",
            }
        )
        return {**state, "cicd_status": "failure", "cicd_timeline": timeline}

    except Exception as exc:
        timeline.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "cicd_error",
                "detail": str(exc),
                "status": "failure",
            }
        )
        return {**state, "cicd_status": "failure", "cicd_timeline": timeline}
