"""
Shared LangGraph state definition for the CI/CD Healing Agent.
Every node reads from and writes to this TypedDict.
"""

from __future__ import annotations
from typing import Any, List, Optional, TypedDict


class FailureEvent(TypedDict):
    """A single test/lint failure discovered during analysis."""
    bug_type: str          # LINTING | SYNTAX | LOGIC | TYPE_ERROR | IMPORT | INDENTATION
    file: str              # relative path, e.g. "src/utils.py"
    line: int              # 1-based line number
    message: str           # raw error message from tool


class FixRecord(TypedDict):
    """A single fix generated and applied by the AI agent."""
    bug_type: str
    file: str
    line: int
    fix_description: str   # human-readable, e.g. "remove the import statement"
    patch: str             # unified diff patch applied to disk
    status: str            # "applied" | "failed"


class CICDEvent(TypedDict):
    """One checkpoint in the CI/CD timeline."""
    timestamp: str         # ISO-8601
    event: str             # e.g. "workflow_triggered", "tests_running", "tests_passed"
    detail: str
    status: str            # "success" | "failure" | "pending" | "running"


class ScoreBreakdown(TypedDict):
    tests_passed_pct: float   # 0-100
    fixes_applied: int
    fix_quality_score: float  # 0-40
    ci_success_bonus: float   # 0 or 20
    base_score: float         # 0-100 (base score before bonuses/penalties)
    speed_bonus: float        # 0 or 10 (if < 5 minutes)
    efficiency_penalty: float # -2 per commit over 20
    total_score: float        # 0-110 (base + bonuses - penalties)


class AgentState(TypedDict):
    # --- Inputs ---
    repo_url: str
    team_name: str
    leader_name: str
    openai_key: str
    retry_limit: int
    github_token: str

    # --- Derived ---
    branch_name: str          # e.g. RIFT_ORGANISERS_SAIYAM_KUMAR_AI_Fix
    clone_path: str           # local temp directory
    language: str             # "python" | "javascript" | "typescript"

    # --- Analysis ---
    failures: List[FailureEvent]
    total_tests: int
    tests_passed: int
    tests_failed: int

    # --- Fixes ---
    fixes: List[FixRecord]

    # --- Git ---
    commit_sha: str
    pr_url: str

    # --- CI/CD ---
    cicd_timeline: List[CICDEvent]
    cicd_status: str          # "pending" | "running" | "success" | "failure"

    # --- Score ---
    score: ScoreBreakdown

    # --- Control ---
    retry_count: int
    status: str               # "running" | "success" | "failed" | "partial"
    error_message: Optional[str]

    # --- Output ---
    run_id: str
    started_at: str
    finished_at: str
    duration_seconds: float
