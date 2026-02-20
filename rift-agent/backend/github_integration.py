"""
GitHub API integration helpers.
"""

from __future__ import annotations

import httpx

GITHUB_API = "https://api.github.com"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_latest_workflow_run(owner: str, repo: str, branch: str, token: str) -> str | None:
    """Return the ID of the most recent workflow run on the given branch."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/actions/runs"
    params = {"branch": branch, "per_page": 1}

    with httpx.Client(timeout=30) as client:
        r = client.get(url, headers=_headers(token), params=params)
        r.raise_for_status()
        data = r.json()
        runs = data.get("workflow_runs", [])
        return str(runs[0]["id"]) if runs else None


def get_workflow_status(owner: str, repo: str, run_id: str, token: str) -> tuple[str, str | None]:
    """Return (status, conclusion) for a workflow run."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/actions/runs/{run_id}"

    with httpx.Client(timeout=30) as client:
        r = client.get(url, headers=_headers(token))
        r.raise_for_status()
        data = r.json()
        return data.get("status", "unknown"), data.get("conclusion")


def create_pr(
    owner: str,
    repo: str,
    branch: str,
    base: str,
    title: str,
    body: str,
    token: str,
) -> str:
    """Open a pull request and return the PR URL."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls"
    payload = {
        "title": title,
        "body": body,
        "head": branch,
        "base": base,
    }

    with httpx.Client(timeout=30) as client:
        r = client.post(url, headers=_headers(token), json=payload)
        r.raise_for_status()
        return r.json().get("html_url", "")
