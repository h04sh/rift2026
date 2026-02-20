"""
LangGraph Orchestrator – Wires all agents into a stateful graph.

Pipeline:
  clone → analyze → fix → git → cicd_monitor → score
         ↑____________________________|  (retry loop, max N times)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from langgraph.graph import END, StateGraph

from agent.state import AgentState
from agent.agents.clone_agent import clone_agent
from agent.agents.analyze_agent import analyze_agent
from agent.agents.fix_agent import fix_agent
from agent.agents.git_agent import git_agent
from agent.agents.cicd_agent import cicd_agent
from agent.agents.score_agent import score_agent


# ---------------------------------------------------------------------------
# Conditional edges
# ---------------------------------------------------------------------------

def should_retry(state: AgentState) -> str:
    """
    After cicd_monitor: decide whether to retry the fix cycle.
    Re-runs analyze → fix → git → cicd if CI failed and retries remain.
    """
    if state.get("status") == "failed":
        return "score"

    retry_count = state.get("retry_count", 0)
    retry_limit = state.get("retry_limit", 5)
    cicd_status = state.get("cicd_status", "failure")

    if cicd_status == "success":
        return "score"

    if retry_count >= retry_limit:
        return "score"

    return "analyze"  # retry


def increment_retry(state: AgentState) -> AgentState:
    """Node injected between cicd→analyze in the retry path."""
    return {
        **state,
        "retry_count": state.get("retry_count", 0) + 1,
        "fixes": [],  # reset fixes for next iteration
    }


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph() -> Any:
    """Compile and return the LangGraph StateGraph."""

    builder = StateGraph(AgentState)

    # Register nodes
    builder.add_node("clone", clone_agent)
    builder.add_node("analyze", analyze_agent)
    builder.add_node("fix", fix_agent)
    builder.add_node("git", git_agent)
    builder.add_node("cicd_monitor", cicd_agent)
    builder.add_node("score", score_agent)
    builder.add_node("increment_retry", increment_retry)

    # Entry
    builder.set_entry_point("clone")

    # Linear path
    builder.add_edge("clone", "analyze")
    builder.add_edge("analyze", "fix")
    builder.add_edge("fix", "git")
    builder.add_edge("git", "cicd_monitor")

    # Conditional: retry or score
    builder.add_conditional_edges(
        "cicd_monitor",
        should_retry,
        {"score": "score", "analyze": "increment_retry"},
    )
    builder.add_edge("increment_retry", "analyze")
    builder.add_edge("score", END)

    return builder.compile()


# ---------------------------------------------------------------------------
# Public run function
# ---------------------------------------------------------------------------

def run_pipeline(
    repo_url: str,
    team_name: str,
    leader_name: str,
    openai_key: str,
    github_token: str = "",
    retry_limit: int = 5,
) -> AgentState:
    """Execute the full CI/CD healing pipeline and return the final state."""

    graph = build_graph()

    initial_state: AgentState = {
        # Inputs
        "repo_url": repo_url,
        "team_name": team_name,
        "leader_name": leader_name,
        "openai_key": openai_key,
        "github_token": github_token,
        "retry_limit": retry_limit,
        # Defaults
        "branch_name": "",
        "clone_path": "",
        "language": "python",
        "failures": [],
        "total_tests": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "fixes": [],
        "commit_sha": "",
        "pr_url": "",
        "cicd_timeline": [],
        "cicd_status": "pending",
        "score": {
            "tests_passed_pct": 0.0,
            "fixes_applied": 0,
            "fix_quality_score": 0.0,
            "ci_success_bonus": 0.0,
            "total_score": 0.0,
        },
        "retry_count": 0,
        "status": "running",
        "error_message": None,
        "run_id": str(uuid.uuid4()),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": "",
        "duration_seconds": 0.0,
    }

    import time
    start_time = time.time()

    final_state = graph.invoke(initial_state)

    elapsed = time.time() - start_time
    final_state["finished_at"] = datetime.now(timezone.utc).isoformat()
    final_state["duration_seconds"] = round(elapsed, 2)

    return final_state
