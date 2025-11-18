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
COPY frontend/yarn.lock* ./

# Install dependencies with npm (more reliable than yarn/corepack in CI/CD)
RUN npm ci --prefer-offline --no-audit --legacy-peer-deps || \
    npm install --legacy-peer-deps

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
