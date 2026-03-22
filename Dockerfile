# Build stage
FROM python:3.13-slim AS builder

# git is required for uv to install immich-sdk from GitHub
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /build

# Copy dependency files and source code
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/

# Install dependencies and package (without dev dependencies).
# --no-editable: install the app into site-packages so copying .venv to /app works;
# editable installs point at /build/src and break at runtime (No module named immich_auto_stacker).
# Use --frozen only if uv.lock exists, otherwise let uv create it
RUN if [ -f uv.lock ]; then \
        uv sync --frozen --no-dev --no-cache --no-editable; \
    else \
        uv sync --no-dev --no-cache --no-editable; \
    fi

# Runtime stage
FROM python:3.13-slim AS runtime

# Set working directory
WORKDIR /app

# Copy installed virtual environment from builder (package is in site-packages, not editable)
COPY --from=builder /build/.venv /app/.venv

# Use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
CMD ["python", "-m", "immich_auto_stacker"]
