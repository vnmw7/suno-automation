# syntax=docker/dockerfile:1
# System: Suno Automation Backend
# Module: Docker Runtime
# File URL: backend/Dockerfile
# Purpose: Build the FastAPI backend container with Camoufox dependencies and health instrumentation.

ARG PYTHON_IMAGE=python:3.11-slim-bookworm

FROM ${PYTHON_IMAGE} AS builder
ARG TARGETARCH
ARG CAMOUFOX_VERSION=135.0.1-beta.24
ARG CAMOUFOX_SOURCE=auto
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CAMOUFOX_INSTALL_ROOT=/build/camoufox-install \
    CAMOUFOX_CACHE_DIR=/root/.cache/camoufox
WORKDIR /build

COPY requirements.txt ./requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir --prefix /install -r requirements.txt \
    && python -m pip install --no-cache-dir --prefix /install "camoufox[geoip]"

ENV PYTHONPATH=/install/lib/python3.11/site-packages

COPY build/artifacts/camoufox/ ./artifacts/camoufox/
RUN set -eux; \
    mkdir -p "${CAMOUFOX_INSTALL_ROOT}"; \
    rm -rf "${CAMOUFOX_INSTALL_ROOT:?}/"*; \
    case "${CAMOUFOX_SOURCE}" in \
      manual) \
        if ! compgen -G "./artifacts/camoufox/*.zip" > /dev/null; then \
          echo "Manual Camoufox archive not found in build/artifacts/camoufox" >&2; \
          exit 1; \
        fi; \
        cp "./artifacts/camoufox/"*.zip camoufox.zip; \
        unzip camoufox.zip -d camoufox-unpacked; \
        cp -a camoufox-unpacked/. "${CAMOUFOX_INSTALL_ROOT}/"; \
        ;; \
      auto) \
        if [ "${TARGETARCH}" = "arm64" ]; then \
          curl -sSL -o camoufox.zip "https://github.com/daijro/camoufox/releases/download/v${CAMOUFOX_VERSION}/camoufox-${CAMOUFOX_VERSION}-lin.arm64.zip"; \
          unzip camoufox.zip -d camoufox-unpacked; \
          cp -a camoufox-unpacked/. "${CAMOUFOX_INSTALL_ROOT}/"; \
        elif [ "${TARGETARCH}" = "amd64" ]; then \
          python -m camoufox fetch; \
          if [ ! -f "${CAMOUFOX_CACHE_DIR}/camoufox-bin" ]; then \
            echo "Camoufox fetch did not install binary at ${CAMOUFOX_CACHE_DIR}/camoufox-bin" >&2; \
            exit 1; \
          fi; \
          cp -a "${CAMOUFOX_CACHE_DIR}/." "${CAMOUFOX_INSTALL_ROOT}/"; \
        else \
          echo "Unsupported architecture: ${TARGETARCH}" >&2; \
          exit 1; \
        fi; \
        ;; \
      *) \
        echo "Unsupported CAMOUFOX_SOURCE=${CAMOUFOX_SOURCE}" >&2; \
        exit 1; \
        ;; \
    esac; \
    CAMOUFOX_VERSION_BASE="${CAMOUFOX_VERSION%%-*}"; \
    CAMOUFOX_RELEASE_PART="${CAMOUFOX_VERSION#*-}"; \
    if [ "${CAMOUFOX_RELEASE_PART}" = "${CAMOUFOX_VERSION_BASE}" ]; then \
      CAMOUFOX_RELEASE_PART="${CAMOUFOX_VERSION_BASE}"; \
    fi; \
    if [ ! -f "${CAMOUFOX_INSTALL_ROOT}/version.json" ]; then \
      printf '{"version": "%s", "release": "%s"}' "${CAMOUFOX_VERSION_BASE}" "${CAMOUFOX_RELEASE_PART}" > "${CAMOUFOX_INSTALL_ROOT}/version.json"; \
    fi; \
    chmod -R 0755 "${CAMOUFOX_INSTALL_ROOT}"; \
    rm -rf camoufox.zip camoufox-unpacked

FROM ${PYTHON_IMAGE} AS macos
ARG TARGETARCH
ARG CAMOUFOX_SOURCE=auto
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/app/.cache/browsers \
    CAMOUFOX_CACHE_DIR=/home/suno-user/.cache/camoufox \
    PATH="/home/suno-user/.local/bin:${PATH}"
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    fonts-liberation \
    fonts-noto-color-emoji \
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
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY --from=builder /build/camoufox-install /opt/camoufox

# Fix browserforge missing data files by downloading them directly
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && \
    mkdir -p /usr/local/lib/python3.11/site-packages/browserforge/headers/data && \
    mkdir -p /usr/local/lib/python3.11/site-packages/browserforge/fingerprints/data && \
    cd /usr/local/lib/python3.11/site-packages/browserforge/headers/data && \
    curl -L -O https://github.com/daijro/browserforge/raw/main/browserforge/headers/data/input-network.zip && \
    curl -L -O https://github.com/daijro/browserforge/raw/main/browserforge/headers/data/header-network.zip && \
    curl -L -O https://github.com/daijro/browserforge/raw/main/browserforge/headers/data/browser-helper-file.json && \
    curl -L -O https://github.com/daijro/browserforge/raw/main/browserforge/headers/data/headers-order.json && \
    cd /usr/local/lib/python3.11/site-packages/browserforge/fingerprints/data && \
    curl -L -O https://github.com/daijro/browserforge/raw/main/browserforge/fingerprints/data/fingerprint-network.zip && \
    apt-get remove -y curl && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash suno-user \
    && mkdir -p /home/suno-user/.cache \
    && cp -a /opt/camoufox /home/suno-user/.cache/camoufox \
    && mkdir -p /home/suno-user/.local/bin \
    && if [ -f /home/suno-user/.cache/camoufox/camoufox ]; then ln -sf /home/suno-user/.cache/camoufox/camoufox /home/suno-user/.local/bin/camoufox; fi \
    && if [ -f /home/suno-user/.cache/camoufox/camoufox-bin ]; then ln -sf /home/suno-user/.cache/camoufox/camoufox-bin /home/suno-user/.local/bin/camoufox-bin; fi \
    && chown -R suno-user:suno-user /home/suno-user /opt/camoufox

COPY --chown=suno-user:suno-user . .

RUN mkdir -p /app/songs /app/camoufox_session_data /app/logs /app/.cache \
    && chown -R suno-user:suno-user /app

USER suno-user

EXPOSE 8000

ENV BACKEND_HEALTH_TIMEOUT=5

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD python -c "import http.client, os, sys; timeout=float(os.getenv('BACKEND_HEALTH_TIMEOUT','5')); conn=http.client.HTTPConnection('127.0.0.1', 8000, timeout=timeout); conn.request('GET', '/health'); status = conn.getresponse().status; sys.exit(0 if 200 <= status < 500 else 1)"

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
