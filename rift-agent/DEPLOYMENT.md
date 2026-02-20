# Deployment Guide — RIFT 2026 CI/CD Healing Agent

---

## Option A: Local Development

### Backend
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # fill in your keys

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env   # set VITE_API_URL=http://localhost:8000
npm run dev
```

Open `http://localhost:5173`

---

## Option B: Docker Compose (Recommended)

```bash
# From project root
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

To stop:
```bash
docker-compose down
```

---

## Option C: Cloud Deployment

### Backend → Railway / Render

1. Push `backend/` folder to a GitHub repo
2. Connect to [Railway](https://railway.app) or [Render](https://render.com)
3. Set environment variables:
   ```
   PORT=8000
   ```
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Note the public URL (e.g. `https://rift-backend.railway.app`)

### Frontend → Vercel

1. Push `frontend/` folder to GitHub
2. Import into [Vercel](https://vercel.com)
3. Set environment variable:
   ```
   VITE_API_URL=https://rift-backend.railway.app
   ```
4. Build command: `npm run build`
5. Output directory: `dist`
6. Deploy — Vercel will give you a public URL

---

## Environment Variables Reference

### Backend (`backend/.env`)
| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o | Optional (falls back to rule-based) |
| `GITHUB_TOKEN` | GitHub PAT for private repos + push | Optional |
| `RETRY_LIMIT` | Default retry limit | Optional (default: 5) |

### Frontend (`frontend/.env`)
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend base URL | `http://localhost:8000` |

---

## Production Checklist

- [ ] Set real OpenAI API key
- [ ] Set GitHub Personal Access Token with `repo` + `workflow` scopes
- [ ] Enable HTTPS on backend (use Railway/Render TLS)
- [ ] Update `VITE_API_URL` to HTTPS backend URL
- [ ] Test `POST /api/run-agent` with a sample public repo
- [ ] Verify branch naming format in dashboard
