# ═══════════════════════════════════════════════════════════════
#  AIC-4 DroneTracking — Professional Production Dockerfile
# ═══════════════════════════════════════════════════════════════

# Global Build Arguments
ARG PYTHON_VERSION=3.10-slim-bookworm
ARG APP_HOME=/app

# ─── Stage 1: Builder ─────────────────────────────────────────
FROM python:${PYTHON_VERSION} AS builder

# Install system build tools
RUN echo "deb https://deb.debian.org/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb https://deb.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb https://deb.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Install dependencies into a wheels directory to avoid copying system junk
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir wheel && \
    pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# ─── Stage 2: Runtime ─────────────────────────────────────────
FROM python:${PYTHON_VERSION} AS runtime

LABEL maintainer="Mohamed Gharieb <ghariebml@github.com>"
LABEL description="AIC-4 Aerial Multi-Object Tracking — AI Pipeline & Dashboard"
LABEL version="1.1.0"

# Python Environment Variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Runtime system libraries
RUN echo "deb https://deb.debian.org/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb https://deb.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb https://deb.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    curl \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN groupadd -g 1000 aic4group && \
    useradd -u 1000 -g aic4group -m -s /bin/bash aic4user

WORKDIR /app

# Install dependencies from builder wheels
COPY --from=builder /build/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Copy project source
COPY . .

# Set permissions for the non-root user
RUN mkdir -p /app/experiments /app/models /app/data /app/configs && \
    chown -R aic4user:aic4group /app && \
    chmod +x /app/scripts/docker-entrypoint.sh

# NOTE: We start as root to handle volume permissions in the entrypoint, 
# then drop to aic4user.
USER root

# Expose dashboard port
EXPOSE 5000

# Use entrypoint script for initialization
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]

# Default: run the dashboard server
CMD ["python", "dashboard/app.py"]

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1
