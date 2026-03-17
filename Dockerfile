# =============================================================================
# ECGiga — Multi-stage Dockerfile
# Stage 1: build  (install dependencies)
# Stage 2: runtime (slim production image)
# =============================================================================

# ---------- Stage 1: Build ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# System deps needed for compilation of some wheels
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc g++ libffi-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Copy source and install the project itself
COPY pyproject.toml setup.cfg* setup.py* ./
COPY . /build/src
RUN pip install --no-cache-dir --prefix=/install -e /build/src || true

# ---------- Stage 2: Runtime ----------
FROM python:3.12-slim AS runtime

# Security: create non-root user
RUN groupadd -r ecgiga && useradd -r -g ecgiga -m ecgiga

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# System runtime deps (OpenCV headless needs libgl)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libsm6 \
        libxrender1 \
        libxext6 \
        curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application code
COPY . .

# Create data directory for SQLite DB and uploads
RUN mkdir -p /app/data && chown -R ecgiga:ecgiga /app

# Expose ports: 8050 for Dash, 8000 for FastAPI MCP server
EXPOSE 8050 8000

# Health check — hit the FastAPI health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER ecgiga

# Default command: run both servers via a simple shell script
# In production, use docker-compose to run them separately
CMD ["sh", "-c", "\
    uvicorn mcp_server:app --host 0.0.0.0 --port 8000 & \
    python -m web_app.dash_app.app --host 0.0.0.0 --port 8050 \
"]
