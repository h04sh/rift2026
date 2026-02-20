# LinkedIn Demo Video Script
## RIFT 2026 – Autonomous CI/CD Healing Agent
### Duration: ~2 minutes 30 seconds

---

## [0:00 – 0:15] HOOK

> (Screen shows the RIFT dashboard, dark glassmorphism UI)

**Voiceover / Caption:**
> "What if your CI/CD pipeline could fix its own bugs — automatically — without any human intervention?"

*Show the dashboard with an animated score card at 97/100.*

---

## [0:15 – 0:40] PROBLEM STATEMENT

> (Slow motion: GitHub PR with tons of test failures, red X marks, engineers frustrated)

**Voiceover:**
> "Every developer knows the pain. You push code, the pipeline breaks, and you spend hours chasing linting errors, syntax bugs, and type mismatches. At RIFT 2026, we decided to solve this problem once and for all."

---

## [0:40 – 1:20] LIVE DEMO — THE AGENT IN ACTION

> (Screen recording of the dashboard)

1. **Paste a GitHub repo URL** into the Input Section.
2. Set team name: `RIFT_ORGANISERS`, leader: `SAIYAM_KUMAR`
3. Click **"Run AI Agent"**

**Voiceover:**
> "The agent clones the repo, runs all tests, and discovers failures — automatically."

*Show the CI/CD Timeline lighting up event by event:*
- 📦 Clone Started…
- 🔍 Analysis — Found 5 failures
- 🤖 AI Fix Generation
- 🌿 Branch Created: `RIFT_ORGANISERS_SAIYAM_KUMAR_AI_Fix`
- 🚀 Code Pushed
- ✅ CI Passed

**Voiceover:**
> "GPT-4o generates a targeted fix for every single failure — LINTING, SYNTAX, TYPE_ERROR, IMPORT, INDENTATION — and commits them to a new branch with a structured commit message."

---

## [1:20 – 1:50] RESULTS REVEAL

> (Scroll through Fixes Applied Table)

**Voiceover:**
> "Every fix is logged in the exact required format:
> 'LINTING error in src/utils.py line 15 → Fix: remove the import statement'
> The Score Breakdown shows us 97.33 out of 100 — 40 points from fix quality, 40 from tests, 20 CI/CD bonus."

*Show the animated radial score rings spinning to their final values.*

---

## [1:50 – 2:15] ARCHITECTURE HIGHLIGHT

> (Show architecture diagram slide or code)

**Voiceover:**
> "Under the hood, this is a LangGraph multi-agent system — six specialized agents wired into a stateful graph with a retry loop. If CI still fails after a fix, the agent retries up to 5 times. The FastAPI backend, React dashboard, and Docker container make this fully production-deployable."

---

## [2:15 – 2:30] CALL TO ACTION

> (Face cam or name card)

**Voiceover / On screen text:**
> "This is our submission for the RIFT 2026 Hackathon — AI/ML × DevOps Automation × Agentic Systems Track.
> Autonomous. Intelligent. Production-ready.
>
> 🔗 GitHub: [your-repo-link]
> 👥 Team: [Your Team Name]
> 🏷 #RIFT2026 #LangGraph #FastAPI #React #DevOps #AIAgent"

---

## Recording Tips
- Use OBS or Loom for screen recording
- Run the agent against a real buggy repo (or use the example in `results.json`)
- Keep background music subtle (lo-fi / cinematic)
- Export at 1080p, 30fps
- Thumbnail: Dashboard screenshot + "97/100 Score" overlay
