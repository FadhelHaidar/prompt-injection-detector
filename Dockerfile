# -----------------------------------------------------------------------------
# Stage 1: Builder (Unchanged)
# -----------------------------------------------------------------------------
FROM public.ecr.aws/docker/library/python:3.12-slim AS builder

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
FROM public.ecr.aws/docker/library/python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/app/model_cache \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# 1. Create non-root user
RUN groupadd -g 1001 ut-dad && \
    useradd -u 1001 -g 1001 -m -d /home/ut-dad -s /bin/bash ut-dad

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
COPY --from=builder --chown=ut-dad:ut-dad /app/.venv /app/.venv
COPY --chown=ut-dad:ut-dad src/ ./src

# 5. Ensure ownership
RUN chown -R ut-dad:ut-dad /app

# Expose port
EXPOSE 8000

# 6. Switch to non-root user
USER ut-dad

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]