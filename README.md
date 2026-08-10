# AI-Powered Disaster Resource Locator

A production-ready, full-stack disaster management system built with **FastAPI** (backend) and **React + Vite** (frontend), deployed as a **single service** on **Render** with **Neon PostgreSQL**.

> **Single-origin architecture:** FastAPI serves both the API (`/api/v1/*`) and the React SPA from one URL. No CORS, no separate frontend hosting, no `VITE_API_URL`.

---

## Project Structure

```
.
├── backend/                 # FastAPI service
│   ├── core/                # config.py, database.py
│   ├── models/              # SQLAlchemy ORM models
│   ├── routers/             # API route handlers
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # gemini_service.py, geo_service.py
│   ├── migrations/          # Alembic (alembic.ini, env.py, versions/)
│   ├── main.py              # FastAPI app — routes + SPA serving
│   └── requirements.txt     # Pinned Python dependencies
├── frontend/                # React (Vite) SPA
│   ├── src/
│   │   ├── api/client.js    # Relative-path API client
│   │   ├── App.jsx          # React Router routes
│   │   └── main.jsx         # Entry point
│   ├── vite.config.js       # Dev proxy to localhost:8000
│   └── package.json
├── Dockerfile               # Multi-stage (Node build → Python runtime)
├── render.yaml              # Single web service
├── .env.example             # DATABASE_URL, GEMINI_API_KEY, JWT_SECRET
└── .gitignore
```

---

## How It Works

`main.py` registers routes in this exact order (order matters!):

1. **API routers** (`/api/v1/reports`, `/api/v1/resources`, etc.) — matched first
2. **Static file mount** (`/assets/*`) — serves Vite's hashed JS/CSS bundles
3. **SPA catch-all** (`/{path}`) — returns `index.html` for any unmatched GET

This means `/api/v1/reports` hits the FastAPI handler, while `/dashboard` returns the React app.

---

## Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| Docker (optional) | 24+ |

---

## Local Development

You run **two terminals** — backend and frontend separately. The Vite dev server proxies `/api/*` requests to the FastAPI backend.

### 1. Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt

# Copy .env.example to backend/.env and fill in values
cp ../.env.example .env
# Edit .env — set DATABASE_URL, GEMINI_API_KEY, JWT_SECRET

# Run migrations
alembic upgrade head

# Start backend
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/api/docs

### 2. Frontend

```bash
cd frontend

npm install

# Start Vite dev server (proxies /api/* to localhost:8000)
npm run dev
```

App: http://localhost:5173

---

## Environment Variables

Only **3 secrets** are needed (set in Render dashboard for production, in `backend/.env` for local dev):

| Variable | Description |
|---|---|
| `DATABASE_URL` | Neon PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `GEMINI_API_KEY` | Google Gemini API key |
| `JWT_SECRET` | Random secret for JWT signing (min 32 chars) |

No `ALLOWED_ORIGINS`, `VITE_API_URL`, or CORS vars — same-origin architecture eliminates them.

---

## Deployment on Render

### Single Service

1. Push to GitHub.
2. In [Render Dashboard](https://dashboard.render.com) → **New → Web Service**.
3. Connect your repo. Render detects `render.yaml` automatically.
4. Add the 3 environment variables (`DATABASE_URL`, `GEMINI_API_KEY`, `JWT_SECRET`).
5. Deploy. Render will:
   - Build the multi-stage Docker image (Node builds React → Python serves everything)
   - Run `alembic upgrade head` on startup
   - Start uvicorn

**One URL** serves both the API and the React frontend.

### Neon PostgreSQL

1. Create a project at [neon.tech](https://neon.tech).
2. Copy the connection string (use `postgresql+asyncpg://` scheme).
3. Set as `DATABASE_URL` in Render environment variables.

---

## Useful Commands

```bash
# Generate a new Alembic migration
cd backend
alembic revision --autogenerate -m "describe_your_change"
alembic upgrade head

# Build frontend for production (testing locally)
cd frontend
npm run build

# Build Docker image locally
docker build -t disaster-locator .
docker run --env-file backend/.env -p 8000:8000 disaster-locator
```

---

## API Endpoints

All endpoints are prefixed with `/api/v1/`:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/v1/reports/` | Create disaster report |
| `GET` | `/api/v1/reports/` | List reports (paginated) |
| `GET` | `/api/v1/reports/{id}` | Get single report |
| `PATCH` | `/api/v1/reports/{id}` | Update report |
| `DELETE` | `/api/v1/reports/{id}` | Delete report |
| `POST` | `/api/v1/resources/` | Register resource |
| `GET` | `/api/v1/resources/` | List resources |
| `GET` | `/api/v1/resources/nearby/{report_id}` | Find nearby resources |
| `POST` | `/api/v1/triage/` | Create triage case |
| `GET` | `/api/v1/triage/` | List triage cases |
| `POST` | `/api/v1/triage/{id}/reclassify` | Re-run AI classification |
| `GET` | `/api/v1/dashboard/stats` | Dashboard statistics |
| `GET` | `/api/v1/dashboard/map-pins` | Map pin locations |

Full interactive docs at `/api/docs` (Swagger UI).

---

## License

MIT
