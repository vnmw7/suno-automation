#!/bin/bash
# System: Suno Automation
# Module: Docker Image Setup
# File URL: scripts/pull-images.sh
# Purpose: Pull Suno Automation frontend and backend Docker images for a chosen registry and tag.

set -euo pipefail

strRegistry="${1:-${SUNO_IMAGE_REGISTRY:-}}"
strTag="${2:-${SUNO_IMAGE_TAG:-latest}}"

if [[ -z "${strRegistry}" ]]; then
    read -r -p "Enter registry (for example, your-namespace): " strRegistry
fi

if [[ -z "${strRegistry}" ]]; then
    echo "Registry is required. Exiting." >&2
    exit 1
fi

if [[ -z "${strTag}" ]]; then
    read -r -p "Enter tag [latest]: " strTag
    if [[ -z "${strTag}" ]]; then
        strTag="latest"
    fi
fi

echo "Pulling frontend image \"${strRegistry}/suno-frontend:${strTag}\"..."
docker pull "${strRegistry}/suno-frontend:${strTag}"

echo "Pulling backend image \"${strRegistry}/suno-backend:${strTag}\"..."
docker pull "${strRegistry}/suno-backend:${strTag}"

echo "Both images pulled successfully."
