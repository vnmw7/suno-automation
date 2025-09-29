# Stage 1: Builder
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Production for Desktop
FROM python:3.11-slim
WORKDIR /app

# Install Camoufox/Firefox dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Core Firefox/Camoufox dependencies
    libgtk-3-0 \
    libasound2 \
    libx11-xcb1 \
    libgbm1 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxkbcommon0 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxss1 \
    libxtst6 \
    libdbus-glib-1-2 \
    # Utilities
    wget \
    curl \
    fonts-liberation \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Create directories for persistent data
RUN mkdir -p /app/songs /app/camoufox_session_data /app/logs

# Copy Python packages from builder
COPY --from=builder /root/.local /usr/local

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH=/usr/local/bin:$PATH
ENV PLAYWRIGHT_BROWSERS_PATH=/app/.cache/browsers
ENV CAMOUFOX_CACHE_DIR=/app/.cache/camoufox

# Pre-fetch Camoufox browser
RUN python -c "from camoufox import fetch; fetch()" || true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]