# Simple root Dockerfile that builds backend
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY backend/ .
ENV PORT=80
EXPOSE 80
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","80"]
