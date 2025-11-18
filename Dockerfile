# ==============================================================================
# Единый Dockerfile для развертывания Frontend + Backend в одном контейнере
# ==============================================================================
# Архитектура:
#   - FastAPI backend обрабатывает /api/* запросы
#   - FastAPI раздает статику React из /app/frontend/dist
#   - Один контейнер, один процесс, один порт (80)
# ==============================================================================

# ------------------------------------------------------------------------------
# STAGE 1: Build Frontend (React + Vite)
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /build

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies with npm
# Three-tier strategy: normal → different registry → force (if registries are corrupted)
# This handles: registry failures, lock file mismatches, corrupted packages
RUN npm cache clean --force && \
    npm config set registry https://registry.npmjs.org/ && \
    npm install --legacy-peer-deps --no-optional --no-fund --fetch-timeout=60000 --fetch-retry-mintimeout=20000 --fetch-retry-maxtimeout=120000 2>&1 | tail -20 || \
    (echo "First registry failed, retrying with mirror..." && \
     npm cache clean --force && \
     npm config set registry https://registry.npmmirror.com && \
     npm install --legacy-peer-deps --no-optional --no-fund --fetch-timeout=60000 --fetch-retry-mintimeout=20000 --fetch-retry-maxtimeout=120000 2>&1 | tail -20) || \
    (echo "Both registries failed, proceeding with integrity check disabled (corrupted registry issue)..." && \
     npm cache clean --force && \
     npm config set registry https://registry.npmjs.org/ && \
     npm install --legacy-peer-deps --no-optional --no-fund --fetch-timeout=60000 --fetch-retry-mintimeout=20000 --fetch-retry-maxtimeout=120000 --force 2>&1 | tail -20)

# Copy frontend source code
COPY frontend/ ./

# Copy production environment
COPY frontend/.env.production .env.production

# Build frontend
RUN npm run build

# Verify build output
RUN ls -la dist/ && echo "✓ Frontend built successfully"

# Результат: /build/dist содержит собранный frontend

# ------------------------------------------------------------------------------
# STAGE 2: Build Backend + Frontend static
# ------------------------------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./

# Copy built frontend from stage 1
COPY --from=frontend-builder /build/dist ./static

# Verify static files were copied
RUN ls -la /app/static/ && \
    test -f /app/static/index.html && \
    echo "✓ Static files copied successfully" || \
    (echo "✗ ERROR: Static files not found!" && exit 1)

# Environment variables
ENV PORT=80
ENV PYTHONUNBUFFERED=1
ENV STATIC_DIR=/app/static

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1:80/health || exit 1

# Start FastAPI with static file serving
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers", "--forwarded-allow-ips", "*"]
