# Simple root Dockerfile that builds backend
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY backend/ .
ENV PORT=80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget -qO- http://127.0.0.1:80/health || exit 1

CMD ["uvicorn","main:app","--host","0.0.0.0","--port","80","--proxy-headers","--forwarded-allow-ips","*"]
