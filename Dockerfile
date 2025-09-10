# Multi-stage build for CRAEFTO Automation Platform
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory and user
RUN groupadd -r craefto && useradd -r -g craefto craefto
WORKDIR /app

# Development stage
FROM base as development

# Install development dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY --chown=craefto:craefto . .

# Switch to non-root user
USER craefto

# Expose port
EXPOSE 8000

# Development command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Install only production dependencies
COPY requirements.txt .
RUN pip install --no-dev -r requirements.txt && \
    pip install gunicorn[gevent]==21.2.0

# Copy source code
COPY --chown=craefto:craefto app/ ./app/
COPY --chown=craefto:craefto *.py ./

# Switch to non-root user
USER craefto

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production command with Gunicorn
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]

# Testing stage
FROM development as testing

# Install testing dependencies
RUN pip install pytest-cov bandit safety

# Run tests
RUN pytest tests/ --cov=app --cov-report=html --cov-report=xml

# Security scan
RUN bandit -r app/ -f json -o bandit-report.json || true
RUN safety check --json --output safety-report.json || true

# Final production image
FROM production as final
