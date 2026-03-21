# Build stage
FROM python:3.13-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /build

# Copy dependency files and source code
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/

# Install dependencies and package (without dev dependencies)
# Use --frozen only if uv.lock exists, otherwise let uv create it
RUN if [ -f uv.lock ]; then \
        uv sync --frozen --no-dev --no-cache; \
    else \
        uv sync --no-dev --no-cache; \
    fi

# Runtime stage
FROM python:3.13-slim AS runtime

# Set working directory
WORKDIR /app

# Copy installed virtual environment from builder
COPY --from=builder /build/.venv /app/.venv

# Copy application source code
COPY src/ ./src/
COPY pyproject.toml ./

# Use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
CMD ["python", "-m", "python-template.main"]

