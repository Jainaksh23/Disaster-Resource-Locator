"""
main.py — FastAPI application entry point.

Serves API routes under /api/v1/* AND the React SPA from frontend/dist.

ROUTE REGISTRATION ORDER IS CRITICAL:
  1. All /api/v1/* routers           ← matched first
  2. Mount /assets as static files   ← Vite hashed bundles (JS, CSS, images)
  3. Catch-all GET /{path}           ← returns index.html for React Router
     ↑ This MUST be last or it will shadow API routes!
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from core.config import get_settings
from routers import auth, dashboard, reports, resources, triage, sop
from services import rag_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()

# Path to the built React app (populated by Dockerfile Stage 1)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting %s v%s [%s]", settings.APP_NAME, settings.APP_VERSION, settings.APP_ENV
    )
    if FRONTEND_DIR.is_dir():
        logger.info("Serving frontend from %s", FRONTEND_DIR)
    else:
        logger.warning("Frontend dist/ not found at %s — SPA routes will 404", FRONTEND_DIR)
        
    # Load FAISS index for RAG (Temporarily Disabled)
    # logger.info("Initializing RAG service...")
    # await rag_service.init_rag()
    
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered disaster resource locator API. "
        "Uses Gemini for triage classification and report summarisation."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. API ROUTERS — must be registered FIRST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
app.include_router(auth.router)         # /api/v1/auth
app.include_router(reports.router)      # /api/v1/reports
app.include_router(resources.router)    # /api/v1/resources
app.include_router(triage.router)       # /api/v1/triage
app.include_router(dashboard.router)    # /api/v1/dashboard
app.include_router(sop.router)          # /api/v1/sop


@app.get("/api/health", tags=["health"])
async def health_check() -> dict:
    """Render health-check endpoint — must return 200."""
    return {"status": "ok", "version": settings.APP_VERSION, "env": settings.APP_ENV}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. STATIC ASSETS — Vite puts hashed bundles in dist/assets/
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if FRONTEND_DIR.is_dir():
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=str(assets_dir)),
            name="static-assets",
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3. SPA CATCH-ALL — must be registered LAST
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(request: Request, full_path: str):
        """
        Return index.html for any non-API, non-asset path.
        This lets React Router handle client-side routing —
        direct URL access to /dashboard, /reports/new, etc. all work,
        and browser refresh doesn't produce a 404.
        """
        # If a real file exists in dist/ (favicon.ico, robots.txt, etc.), serve it
        file_path = FRONTEND_DIR / full_path
        if full_path and file_path.is_file():
            return FileResponse(str(file_path))
        # Otherwise, hand off to React Router
        return FileResponse(str(FRONTEND_DIR / "index.html"))
