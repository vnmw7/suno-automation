#!/bin/bash
# System: Suno Automation
# Module: Docker Image Setup
# File URL: scripts/start-containers.sh
# Purpose: Start Suno Automation frontend and backend containers and stream their logs.

set -euo pipefail

strFrontendImage="${1:-${SUNO_FRONTEND_IMAGE:-suno-frontend:latest}}"
strBackendImage="${2:-${SUNO_BACKEND_IMAGE:-suno-backend:latest}}"

strFrontendName="suno-frontend-startup"
strBackendName="suno-backend-startup"

cleanup() {
  docker stop "${strFrontendName}" >/dev/null 2>&1 || true
  docker stop "${strBackendName}" >/dev/null 2>&1 || true
  if [[ -n "${intFrontendLogPid:-}" ]]; then
    kill "${intFrontendLogPid}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${intBackendLogPid:-}" ]]; then
    kill "${intBackendLogPid}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

echo "Stopping any existing containers named ${strFrontendName} and ${strBackendName}..."
docker rm -f "${strFrontendName}" >/dev/null 2>&1 || true
docker rm -f "${strBackendName}" >/dev/null 2>&1 || true

echo "Starting frontend container ${strFrontendImage}..."
docker run --rm -d --name "${strFrontendName}" -p 3001:3000 "${strFrontendImage}"

echo "Starting backend container ${strBackendImage}..."
docker run --rm -d --name "${strBackendName}" -p 8000:8000 "${strBackendImage}"

echo "Streaming logs. Press Ctrl+C to stop both containers."
docker logs "${strFrontendName}" --follow --details --timestamps &
intFrontendLogPid=$!

docker logs "${strBackendName}" --follow --details --timestamps &
intBackendLogPid=$!

wait
