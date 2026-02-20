# 🤖 RIFT 2026 — Autonomous CI/CD Healing Agent

> **Track:** AI/ML • DevOps Automation • Agentic Systems  
> **Event:** RIFT 2026 Hackathon  

An autonomous AI agent that clones a GitHub repository, discovers test failures, generates targeted code fixes using GPT-4o, pushes them to a correctly-named branch, monitors CI/CD, and displays everything in a production-ready React dashboard.

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Dashboard (Vite)                   │
│  InputSection │ RunSummaryCard │ ScoreBreakdown             │
│  FixesTable   │ CICDTimeline                                │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API (HTTP)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               FastAPI Backend (Python 3.12)                 │
│  POST /api/run-agent   GET /api/results   GET /api/status   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              LangGraph Multi-Agent Pipeline                 │
│                                                             │
│  ┌────────┐  ┌─────────┐  ┌────────┐  ┌────────────────┐  │
│  │ Clone  │→ │ Analyze │→ │  Fix   │→ │      Git       │  │
│  │ Agent  │  │  Agent  │  │ Agent  │  │ Branch+Commit  │  │
│  └────────┘  └─────────┘  └───┬────┘  └───────┬────────┘  │
│                    ▲           │                │           │
│                    │   Retry   │                ▼           │
│            (up to 5x)◄─────── ▼         ┌──────────────┐  │
│                         ┌──────────┐    │ CICD Monitor │  │
│                         │  Score   │◄───│  (GitHub API)│  │
│                         │  Agent   │    └──────────────┘  │
│                         └──────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 Multi-Agent Architecture

| Agent | Role | Tools |
|-------|------|-------|
| **Clone Agent** | Clones repo, detects language | `git clone`, pathlib |
| **Analyze Agent** | Runs tests, parses failures | `pytest`, `flake8`, `jest`, `eslint` |
| **Fix Agent** | Generates & applies AI patches | OpenAI GPT-4o, rule-based fallback |
| **Git Agent** | Creates branch, commits, pushes | `git`, GitHub API |
| **CI/CD Agent** | Polls GitHub Actions | GitHub REST API |
| **Score Agent** | Calculates composite score | Scoring formula |

**Retry Loop:** After CI/CD monitoring, if tests still fail and `retry_count < retry_limit`, the pipeline loops back to Analyze → Fix → Git → CI/CD (up to 5 times by default).

---

## 📂 Project Structure

```
rift-agent/
├── backend/
│   ├── main.py                      # FastAPI app
│   ├── github_integration.py        # GitHub API helpers
│   ├── results.py                   # results.json writer
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── agent/
│       ├── state.py                 # LangGraph AgentState TypedDict
│       ├── orchestrator.py          # StateGraph pipeline
│       └── agents/
│           ├── clone_agent.py
│           ├── analyze_agent.py
│           ├── fix_agent.py
│           ├── git_agent.py
│           ├── cicd_agent.py
│           └── score_agent.py
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── .env.example
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── store/agentStore.js      # Zustand state
│       ├── api/agentApi.js          # Axios API layer
│       └── components/
│           ├── InputSection.jsx
│           ├── RunSummaryCard.jsx
│           ├── ScoreBreakdown.jsx
│           ├── FixesTable.jsx
│           └── CICDTimeline.jsx
├── docker-compose.yml
├── results.json                     # Example output
├── README.md
├── DEPLOYMENT.md
└── DEMO_SCRIPT.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Git
- Docker (optional)

### 1. Clone & Configure
```bash
git clone <this-repo>
cd rift-agent
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Edit backend/.env with your OpenAI key and GitHub token
```

### 2. Run Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Run Frontend
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

### 4. Docker (all-in-one)
```bash
docker-compose up --build
```

---

## 🔀 Branch Naming
```
TEAM_NAME_LEADER_NAME_AI_Fix
```
- UPPERCASE
- Spaces → underscores
- **Example:** `RIFT_ORGANISERS_SAIYAM_KUMAR_AI_Fix`

## 📝 Commit Format
```
[AI-AGENT] Fix: <clear explanation>
```

## 📋 Test Case Output Format
```
LINTING error in src/utils.py line 15 → Fix: remove the import statement
SYNTAX error in src/validator.py line 8 → Fix: add the colon at the correct position
```

## 🐛 Supported Bug Types
`LINTING` • `SYNTAX` • `LOGIC` • `TYPE_ERROR` • `IMPORT` • `INDENTATION`

---

## 🏆 Scoring

| Component | Points | Criteria |
|-----------|--------|----------|
| Tests Passed | 40 pts | `(passed / total) × 40` |
| Fix Quality | 40 pts | `(applied_fixes / failures) × 40` |
| CI/CD Bonus | 20 pts | 20 if CI passes, else 0 |
| **Total** | **100 pts** | |

---

## 🌐 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/run-agent` | Start the pipeline |
| `GET` | `/api/status` | Poll pipeline status |
| `GET` | `/api/results` | Get full results |
| `GET` | `/api/timeline` | Get CI/CD timeline (live) |
| `GET` | `/health` | Health check |

### POST /api/run-agent payload
```json
{
  "repo_url": "https://github.com/owner/repo",
  "team_name": "RIFT_ORGANISERS",
  "leader_name": "SAIYAM_KUMAR",
  "openai_key": "sk-...",
  "github_token": "ghp_...",
  "retry_limit": 5
}
```

---

## 👥 Team
> Fill in your team details here for the hackathon submission.

- **Team Name:** _______________
- **Leader:** _______________
- **Members:** _______________
- **Track:** AI/ML • DevOps Automation • Agentic Systems

---

## 📄 License
MIT License — Built for RIFT 2026 Hackathon
