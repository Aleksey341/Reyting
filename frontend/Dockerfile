# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
# Vite reads VITE_* from .env and environment during build
RUN npm run build

# Runtime stage - Nginx for static files + proxy to backend
FROM nginx:alpine
# Copy Nginx config (proxies /api to backend)
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Copy built frontend static files
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null 2>&1 || exit 1
