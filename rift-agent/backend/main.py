"""
FastAPI Backend – Main entry point for the RIFT 2026 CI/CD Healing Agent.

Endpoints:
  POST /api/run-agent   – Start the agent pipeline
  GET  /api/results     – Get the latest results.json
  GET  /api/status      – Get current pipeline status
  GET  /health          – Health check
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

from agent.orchestrator import run_pipeline
from results import write_results, RESULTS_PATH

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="RIFT 2026 – Autonomous CI/CD Healing Agent",
    description="AI-powered agent that detects, fixes, and pushes code repairs autonomously.",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory pipeline state (single-run server)
# ---------------------------------------------------------------------------

_pipeline_state: dict = {
    "status": "idle",
    "run_id": None,
    "data": None,
    "error": None,
}
_pipeline_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class RunAgentRequest(BaseModel):
    repo_url: str
    team_name: str = "RIFT_TEAM"
    leader_name: str = "LEADER"
    openai_key: str = ""
    github_token: str = ""
    retry_limit: int = 5


class StatusResponse(BaseModel):
    status: str
    run_id: str | None
    started_at: str | None
    message: str


# ---------------------------------------------------------------------------
# Background task
# ---------------------------------------------------------------------------

def _run_pipeline_task(request: RunAgentRequest) -> None:
    """Execute the LangGraph pipeline in a background thread."""
    global _pipeline_state

    with _pipeline_lock:
        _pipeline_state["status"] = "running"
        _pipeline_state["error"] = None

    try:
        final_state = run_pipeline(
            repo_url=request.repo_url,
            team_name=request.team_name,
            leader_name=request.leader_name,
            openai_key=request.openai_key,
            github_token=request.github_token,
            retry_limit=request.retry_limit,
        )
        write_results(final_state)

        with _pipeline_lock:
            _pipeline_state["status"] = final_state.get("status", "unknown")
            _pipeline_state["run_id"] = final_state.get("run_id")
            _pipeline_state["data"] = final_state

    except Exception as exc:
        with _pipeline_lock:
            _pipeline_state["status"] = "failed"
            _pipeline_state["error"] = str(exc)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "service": "RIFT CI/CD Healing Agent", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/api/run-agent")
def run_agent(request: RunAgentRequest, background_tasks: BackgroundTasks):
    """Trigger the autonomous healing pipeline."""
    global _pipeline_state

    with _pipeline_lock:
        if _pipeline_state["status"] == "running":
            raise HTTPException(
                status_code=409,
                detail="Pipeline is already running. Wait for it to complete.",
            )
        _pipeline_state["status"] = "queued"
        _pipeline_state["run_id"] = None
        _pipeline_state["data"] = None
        _pipeline_state["error"] = None

    background_tasks.add_task(_run_pipeline_task, request)

    return {
        "message": "Pipeline started successfully",
        "status": "queued",
        "docs": "/docs",
    }


@app.get("/api/status")
def get_status() -> StatusResponse:
    """Get current pipeline execution status."""
    with _pipeline_lock:
        state = _pipeline_state.copy()

    data = state.get("data") or {}
    return StatusResponse(
        status=state["status"],
        run_id=state.get("run_id"),
        started_at=data.get("started_at"),
        message=state.get("error") or f"Pipeline is {state['status']}",
    )


@app.get("/api/results")
def get_results():
    """Return the latest results.json."""
    with _pipeline_lock:
        if _pipeline_state["data"]:
            return _pipeline_state["data"]

    if RESULTS_PATH.exists():
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    raise HTTPException(status_code=404, detail="No results available yet. Run the agent first.")


@app.get("/api/timeline")
def get_timeline():
    """Return just the CI/CD timeline for live updates."""
    with _pipeline_lock:
        data = _pipeline_state.get("data") or {}
        status = _pipeline_state.get("status", "idle")

    return {
        "status": status,
        "timeline": data.get("cicd_timeline", []),
    }


@app.post("/api/reset")
def reset_pipeline():
    """Reset the pipeline state to idle."""
    global _pipeline_state
    
    with _pipeline_lock:
        _pipeline_state = {
            "status": "idle",
            "run_id": None,
            "data": None,
            "error": None,
        }
    
    return {
        "message": "Pipeline reset successfully",
        "status": "idle",
    }
