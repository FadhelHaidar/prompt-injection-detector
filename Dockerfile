# Use the official Python 3.12 slim image (matches your .python-version)
FROM python:3.12-slim

# Copy the uv binary from the official uv image
# This is the recommended way to install uv in Docker
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Set Hugging Face cache to a writable directory
    HF_HOME=/app/model_cache \
    # Add the virtual environment to the PATH
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install system dependencies required for ONNX Runtime/Machine Learning libraries
# libgomp1 is often needed for optimized math operations in standard-slim images
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition files first (for Docker layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies using u
RUN uv sync --frozen --no-cache

# Copy the source code
COPY src/ ./src

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# We reference src.main because the file is inside the src directory
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]