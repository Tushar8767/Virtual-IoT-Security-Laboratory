# ============================================================
# Virtual IoT Security Laboratory — All-in-One Dockerfile
# Builds React Frontend + Runs FastAPI Backend in a Single Service
# ============================================================

# --- Stage 1: Build React 19 Frontend ---
FROM node:20-alpine AS frontend-builder
WORKDIR /build

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# --- Stage 2: Install Python Backend Dependencies ---
FROM python:3.12-slim AS backend-builder
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Stage 3: Unified Final Production Container ---
FROM python:3.12-slim
WORKDIR /app

COPY --from=backend-builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Copy backend source code
COPY backend/ /app/backend/
COPY .env.example /app/.env.example

# Copy compiled frontend assets into /app/frontend_dist
COPY --from=frontend-builder /build/dist /app/frontend_dist

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
