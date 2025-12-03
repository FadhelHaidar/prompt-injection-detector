# -----------------------------------------------------------------------------
# Stage 1: Builder (Unchanged)
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Copy uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Set env vars to ensure uv works efficiently
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# -----------------------------------------------------------------------------
# Stage 2: Runner (Final Image)
# -----------------------------------------------------------------------------
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/app/model_cache \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# 1. Create non-root user
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -s /bin/bash --no-create-home appuser

# 2. Install runtime dependencies AND debug tools
#    We do this while still root.
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Required System Deps
    libgomp1 \
    # Debug Tools
    curl \
    wget \
    iputils-ping \
    telnet \
    dnsutils \
    net-tools \
    procps \
    vim \
    && rm -rf /var/lib/apt/lists/*

# 3. Create model cache
RUN mkdir -p /app/model_cache

# 4. Copy files
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser src/ ./src

# 5. Ensure ownership
RUN chown -R appuser:appuser /app

# Expose port
EXPOSE 8000

# 6. Switch to non-root user
USER appuser

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]