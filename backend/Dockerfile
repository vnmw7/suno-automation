# syntax=docker/dockerfile:1

# Stage 1: install Python dependencies into a relocatable prefix
FROM python:3.11-slim AS builder
WORKDIR /app
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir --prefix /install -r requirements.txt

# Stage 2: runtime image for the backend API server
FROM python:3.11-slim
WORKDIR /app

# Install Camoufox/Firefox runtime dependencies needed for headless execution
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    unzip \
    xz-utils \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libdbus-1-3 \
    libdbus-glib-1-2 \
    libdrm2 \
    libgbm1 \
    libgl1 \
    libglu1-mesa \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-6 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    libxshmfence1 \
    libxss1 \
    libxt6 \
    libxtst6 \
    fonts-liberation \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# Mirror the install from the builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Configure runtime environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:${PATH}" \
    PLAYWRIGHT_BROWSERS_PATH=/app/.cache/browsers \
    CAMOUFOX_CACHE_DIR=/app/.cache/camoufox

# Create directories for persistent volumes
RUN mkdir -p /app/songs /app/camoufox_session_data /app/logs /app/.cache

# Pre-fetch the Camoufox browser so the container is ready on first boot.
RUN python -c "from camoufox import fetch; fetch()" || true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import http.client, sys; conn=http.client.HTTPConnection('127.0.0.1', 8000, timeout=5); conn.request('GET', '/'); status = conn.getresponse().status; sys.exit(0 if 200 <= status < 500 else 1)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
