# ── Build stage ──────────────────────────────────────────
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code
COPY . .

# Create a non-root user
RUN adduser --disabled-password --no-create-home appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

# Expose port (DigitalOcean App Platform expects 8080 by default)
EXPOSE 8080

# Production server with gunicorn + uvicorn workers
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-"]
