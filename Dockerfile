# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Copy uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Set env vars to ensure uv works efficiently
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies
# 1. Copy only lockfiles first (caching)
COPY pyproject.toml uv.lock ./

# 2. Install dependencies into a virtual environment
#    --frozen: strictly adhere to uv.lock
#    --no-dev: EXCLUDE development dependencies (huge space saver)
#    --no-install-project: Do not install the current project package yet, just deps
RUN uv sync --frozen --no-dev --no-install-project

# -----------------------------------------------------------------------------
# Stage 2: Runner (Final Image)
# -----------------------------------------------------------------------------
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/app/model_cache \
    # Add the virtual environment to the PATH
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install ONLY runtime system dependencies
# Clean up immediately to reduce layer size
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy the source code
COPY src/ ./src

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]