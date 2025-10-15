#!/bin/bash
# System: Suno Automation
# Module: Docker Image Setup
# File URL: scripts/pull-images.sh
# Purpose: Pull Suno Automation frontend and backend Docker images for a chosen registry and tag.

set -euo pipefail

echo "========================================"
echo "Suno Docker Pull Images Script"
echo "========================================"
echo ""
echo "[DEBUG] Script started at $(date)"
echo ""

# Check Docker availability
echo "[DEBUG] Checking Docker availability..."
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed or not in PATH" >&2
    echo "Please install Docker and ensure it's running" >&2
    exit 1
fi
echo "[SUCCESS] Docker is available ($(docker --version))"
echo ""

# Check if Docker daemon is running
echo "[DEBUG] Checking Docker daemon status..."
if ! docker info &> /dev/null; then
    echo "[ERROR] Docker daemon is not running" >&2
    echo "Please start Docker Desktop or Docker service" >&2
    exit 1
fi
echo "[SUCCESS] Docker daemon is running"
echo ""

# Process input parameters
echo "[DEBUG] Processing input parameters..."
# Automatically use vnmw7 as default registry if not specified
strRegistry="${1:-${SUNO_IMAGE_REGISTRY:-vnmw7}}"
# Automatically use latest as default tag if not specified
strTag="${2:-${SUNO_IMAGE_TAG:-latest}}"

echo "[DEBUG] Input parameter 1 (registry): ${1:-<not provided>}"
echo "[DEBUG] Input parameter 2 (tag): ${2:-<not provided>}"
echo "[DEBUG] Environment SUNO_IMAGE_REGISTRY: ${SUNO_IMAGE_REGISTRY:-<not set>}"
echo "[DEBUG] Environment SUNO_IMAGE_TAG: ${SUNO_IMAGE_TAG:-<not set>}"
echo ""

# Show what defaults are being used
if [[ "${1:-}" == "" ]] && [[ "${SUNO_IMAGE_REGISTRY:-}" == "" ]]; then
    echo "[INFO] No registry provided - using default: vnmw7"
fi
if [[ "${2:-}" == "" ]] && [[ "${SUNO_IMAGE_TAG:-}" == "" ]]; then
    echo "[INFO] No tag provided - using default: latest"
fi

echo "[DEBUG] Using registry: ${strRegistry}"
echo "[DEBUG] Using tag: ${strTag}"
echo ""

echo "========================================"
echo "AUTOMATIC PULL MODE"
echo "========================================"
echo "Target Images:"
echo " - ${strRegistry}/suno-frontend:${strTag}"
echo " - ${strRegistry}/suno-backend:${strTag}"
echo "========================================"
echo ""

echo "========================================"
echo "Starting Docker pulls..."
echo "========================================"
echo ""

# Pull frontend image
echo "[ACTION] Pulling frontend image \"${strRegistry}/suno-frontend:${strTag}\"..."
echo "[DEBUG] Executing: docker pull \"${strRegistry}/suno-frontend:${strTag}\""
if docker pull "${strRegistry}/suno-frontend:${strTag}"; then
    echo "[SUCCESS] Frontend image pulled successfully"
else
    echo "[ERROR] Failed to pull frontend image" >&2
    echo "Common issues:" >&2
    echo "- Invalid registry name" >&2
    echo "- Network connectivity issues" >&2
    echo "- Authentication required for private registry" >&2
    exit 1
fi
echo ""

# Pull backend image
echo "[ACTION] Pulling backend image \"${strRegistry}/suno-backend:${strTag}\"..."
echo "[DEBUG] Executing: docker pull \"${strRegistry}/suno-backend:${strTag}\""
if docker pull "${strRegistry}/suno-backend:${strTag}"; then
    echo "[SUCCESS] Backend image pulled successfully"
else
    echo "[ERROR] Failed to pull backend image" >&2
    echo "Common issues:" >&2
    echo "- Invalid registry name" >&2
    echo "- Network connectivity issues" >&2
    echo "- Authentication required for private registry" >&2
    exit 1
fi
echo ""

echo "========================================"
echo "[SUCCESS] Both images pulled successfully!"
echo "========================================"
echo "[DEBUG] Script completed at $(date)"
echo ""

# List the pulled images
echo "[DEBUG] Verifying pulled images:"
docker images | grep "${strRegistry}/suno" || echo "[WARNING] Could not list images"
