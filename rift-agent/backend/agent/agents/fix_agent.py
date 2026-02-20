"""
Fix Agent – Node 3 of the LangGraph pipeline.

Responsibilities:
  • For each FailureEvent, call OpenAI GPT-4o (or fallback rule-based fixer)
  • Apply the patch to disk
  • Return structured FixRecord list with output format matching:
    "LINTING error in src/utils.py line 15 → Fix: remove the import statement"
"""

from __future__ import annotations

import os
import re
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from agent.state import AgentState, FailureEvent, FixRecord


# ---------------------------------------------------------------------------
# OpenAI integration
# ---------------------------------------------------------------------------

def _call_llm(prompt: str, openai_key: str) -> str:
    """Call OpenAI GPT-4o and return the assistant response text."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=openai_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert software engineer specializing in automated code repair. "
                        "When given a code snippet and an error, you must:\n"
                        "1. Provide a one-line fix description in the format: "
                        "'remove the import statement' or 'add the colon at the correct position'\n"
                        "2. Provide the corrected code ONLY (no explanation, no markdown fences).\n"
                        "Return EXACTLY two sections separated by '---FIX_DESC---' and '---FIXED_CODE---'."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1024,
            temperature=0.1,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        return f"---FIX_DESC---rule-based fix applied\n---FIXED_CODE---# LLM error: {exc}"


def _parse_llm_response(response: str) -> tuple[str, str]:
    """Split LLM response into (fix_description, fixed_code)."""
    desc_match = re.search(r"---FIX_DESC---(.*?)(?=---FIXED_CODE---|$)", response, re.DOTALL)
    code_match = re.search(r"---FIXED_CODE---(.*?)$", response, re.DOTALL)
    fix_desc = desc_match.group(1).strip() if desc_match else "apply automated fix"
    fixed_code = code_match.group(1).strip() if code_match else ""
    return fix_desc, fixed_code


# ---------------------------------------------------------------------------
# Rule-based fallback fixers (for common patterns without LLM)
# ---------------------------------------------------------------------------

RULE_BASED_FIXES: dict[str, dict] = {
    "INDENTATION": {
        "description": "fix indentation to use 4 spaces consistently",
        "pattern": r"^\t+",
        "transform": lambda line: re.sub(r"^\t", "    ", line),
    },
}


def _rule_based_fix(failure: "FailureEvent", code_lines: List[str]) -> tuple[str, List[str]]:
    """Apply a simple rule-based transformation and return (description, new_lines)."""
    bug_type = failure["bug_type"]
    line_idx = failure["line"] - 1

    if bug_type == "INDENTATION" and 0 <= line_idx < len(code_lines):
        fixed_lines = code_lines[:]
        fixed_lines[line_idx] = re.sub(r"^\t+", lambda m: "    " * len(m.group()), code_lines[line_idx])
        return "fix indentation to use 4 spaces consistently", fixed_lines

    if bug_type == "IMPORT" and 0 <= line_idx < len(code_lines):
        fixed_lines = code_lines[:]
        fixed_lines[line_idx] = "# " + code_lines[line_idx].rstrip() + "  # removed unused import\n"
        return "remove the unused import statement", fixed_lines

    return "apply automated fix", code_lines


# ---------------------------------------------------------------------------
# Core fix logic
# ---------------------------------------------------------------------------

def _read_file_lines(filepath: str) -> List[str]:
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()


def _write_file_lines(filepath: str, lines: List[str]) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)


def _apply_fix(
    failure: "FailureEvent",
    clone_path: str,
    openai_key: str,
) -> "FixRecord":
    """Generate and apply one fix. Returns a FixRecord."""

    abs_path = str(Path(clone_path) / failure["file"])
    if not Path(abs_path).exists():
        # Try finding the file relative to clone_path
        candidates = list(Path(clone_path).rglob(Path(failure["file"]).name))
        abs_path = str(candidates[0]) if candidates else abs_path

    if not Path(abs_path).exists():
        return {
            "bug_type": failure["bug_type"],
            "file": failure["file"],
            "line": failure["line"],
            "fix_description": "file not found – skipped",
            "patch": "",
            "status": "failed",
        }

    original_lines = _read_file_lines(abs_path)

    if openai_key and openai_key.startswith("sk-"):
        # Build context window (±10 lines around the error)
        start = max(0, failure["line"] - 11)
        end = min(len(original_lines), failure["line"] + 10)
        context = "".join(original_lines[start:end])
        prompt = textwrap.dedent(f"""
            Bug Type: {failure["bug_type"]}
            File: {failure["file"]}
            Line: {failure["line"]}
            Error Message: {failure["message"]}

            Code context (lines {start+1}-{end}):
            ```
            {context}
            ```

            Provide the fix description and the corrected version of ONLY the code context above.
        """)
        llm_response = _call_llm(prompt, openai_key)
        fix_desc, fixed_code = _parse_llm_response(llm_response)

        if fixed_code:
            # Replace the context window in original file
            fixed_lines = list(original_lines)
            replacement = fixed_code.splitlines(keepends=True)
            fixed_lines[start:end] = replacement
            try:
                _write_file_lines(abs_path, fixed_lines)
                return {
                    "bug_type": failure["bug_type"],
                    "file": failure["file"],
                    "line": failure["line"],
                    "fix_description": fix_desc,
                    "patch": fixed_code,
                    "status": "applied",
                }
            except Exception as exc:
                return {
                    "bug_type": failure["bug_type"],
                    "file": failure["file"],
                    "line": failure["line"],
                    "fix_description": f"LLM fix write error: {exc}",
                    "patch": "",
                    "status": "failed",
                }

    # --- Fallback: rule-based ---
    fix_desc, fixed_lines = _rule_based_fix(failure, original_lines)
    try:
        _write_file_lines(abs_path, fixed_lines)
        return {
            "bug_type": failure["bug_type"],
            "file": failure["file"],
            "line": failure["line"],
            "fix_description": fix_desc,
            "patch": "".join(fixed_lines),
            "status": "applied",
        }
    except Exception as exc:
        return {
            "bug_type": failure["bug_type"],
            "file": failure["file"],
            "line": failure["line"],
            "fix_description": f"rule-based fix error: {exc}",
            "patch": "",
            "status": "failed",
        }


# ---------------------------------------------------------------------------
# Node entry point
# ---------------------------------------------------------------------------

def fix_agent(state: "AgentState") -> "AgentState":
    """LangGraph node: generate and apply AI fixes for all discovered failures."""

    failures = state.get("failures", [])
    clone_path = state.get("clone_path", "")
    openai_key = state.get("openai_key", "")
    timeline = list(state.get("cicd_timeline", []))

    if not failures or state.get("status") == "failed":
        return state

    timeline.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "fix_started",
            "detail": f"Generating AI fixes for {len(failures)} failure(s)",
            "status": "running",
        }
    )

    fixes: List[FixRecord] = []
    for failure in failures:
        fix = _apply_fix(failure, clone_path, openai_key)
        fixes.append(fix)

    applied = sum(1 for f in fixes if f["status"] == "applied")

    timeline.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "fix_complete",
            "detail": f"Applied {applied}/{len(fixes)} fix(es) successfully",
            "status": "success" if applied > 0 else "failure",
        }
    )

    return {
        **state,
        "fixes": fixes,
        "cicd_timeline": timeline,
    }
