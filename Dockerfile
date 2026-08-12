# ── Stage 1: Build React frontend ─────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install deps first (layer caching)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts

# Copy source and build
COPY frontend/ ./
RUN npm run build
# → produces /app/frontend/dist/


# ── Stage 2: Python runtime ──────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# System deps for asyncpg / cryptography wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Never run as root in production
RUN useradd --no-create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Render injects PORT env var; fall back to 8000 locally.
# Run alembic migrations, then start uvicorn.
CMD ["sh", "-c", "cd backend && alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
