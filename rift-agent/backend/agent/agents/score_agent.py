"""
Score Agent – Node 6 of the LangGraph pipeline.

Scoring formula (base 100 points + bonuses/penalties):
  • Base Score (100 pts):
    - Tests Passed (40 pts): (tests_passed / total_tests) * 40
    - Fix Quality (40 pts): (applied_fixes / total_failures) * 40
    - CI/CD Success (20 pts): 20 if CI status == "success", 0 otherwise
  
  • Speed Bonus (+10 pts): +10 if duration < 5 minutes (300 seconds)
  • Efficiency Penalty: -2 points per commit over 20 commits
  
  • Maximum possible score: 110 points (100 base + 10 speed bonus)

Returns a ScoreBreakdown dict.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.state import AgentState, ScoreBreakdown


def score_agent(state: "AgentState") -> "AgentState":
    """LangGraph node: calculate composite score with bonuses and penalties."""

    total_tests = state.get("total_tests", 0)
    tests_passed = state.get("tests_passed", 0)
    failures = state.get("failures", [])
    fixes = state.get("fixes", [])
    cicd_status = state.get("cicd_status", "failure")
    timeline = list(state.get("cicd_timeline", []))
    duration_seconds = state.get("duration_seconds", 0)
    retry_count = state.get("retry_count", 0)

    # --- Tests Passed component (max 40) ---
    if total_tests > 0:
        tests_passed_pct = (tests_passed / total_tests) * 100
        tests_score = (tests_passed / total_tests) * 40
    else:
        # No test suite found – if no failures, assume perfect code
        if len(failures) == 0:
            tests_passed_pct = 100.0
            tests_score = 40.0
        else:
            tests_passed_pct = 0.0
            tests_score = 0.0

    # --- Fix Quality component (max 40) ---
    applied_fixes = sum(1 for f in fixes if f.get("status") == "applied")
    total_failures = len(failures)
    
    if total_failures > 0:
        fix_quality_score = (applied_fixes / total_failures) * 40
    else:
        # No failures found = perfect code = full score
        fix_quality_score = 40.0

    # --- CI/CD Success (max 20) ---
    if cicd_status == "success":
        ci_bonus = 20.0
    elif total_failures == 0 and total_tests == 0:
        # No failures, no tests, but code is clean - give CI bonus
        ci_bonus = 20.0
    else:
        ci_bonus = 0.0

    # --- Base Score (100 points) ---
    base_score = tests_score + fix_quality_score + ci_bonus

    # --- Speed Bonus (+10 if < 5 minutes) ---
    speed_bonus = 10.0 if duration_seconds < 300 else 0.0

    # --- Efficiency Penalty (-2 per commit over 20) ---
    # Count commits from retry_count (each retry = 1 commit)
    total_commits = retry_count + 1  # Initial commit + retries
    efficiency_penalty = max(0, (total_commits - 20) * 2)

    # --- Final Total Score ---
    total_score = round(max(0, base_score + speed_bonus - efficiency_penalty), 2)

    breakdown: "ScoreBreakdown" = {
        "tests_passed_pct": round(tests_passed_pct, 1),
        "fixes_applied": applied_fixes,
        "fix_quality_score": round(fix_quality_score, 2),
        "ci_success_bonus": ci_bonus,
        "base_score": round(base_score, 2),
        "speed_bonus": speed_bonus,
        "efficiency_penalty": efficiency_penalty,
        "total_score": total_score,
    }

    timeline.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "score_calculated",
            "detail": (
                f"Score: {total_score}/110 | "
                f"Base: {base_score:.1f}/100 | "
                f"Speed Bonus: +{speed_bonus} | "
                f"Efficiency Penalty: -{efficiency_penalty}"
            ),
            "status": "success",
        }
    )

    return {
        **state,
        "score": breakdown,
        "cicd_timeline": timeline,
        "status": "success" if total_score >= 50 else "partial",
    }
