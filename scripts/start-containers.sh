#!/bin/bash
# System: Suno Automation
# Module: Docker Container Management
# File URL: scripts/start-containers.sh
# Purpose: Start Suno Automation containers with embedded configuration, robust logging, and automatic setup

set -euo pipefail

echo "========================================"
echo "SUNO AUTOMATION CONTAINER STARTUP"
echo "========================================"
echo ""

# Set up paths and defaults
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "${SCRIPT_DIR}")"
LOG_DIR="${BASE_DIR}/logs"
LOG_FILE="${LOG_DIR}/containers_${TIMESTAMP}.log"

# Inline environment configuration used when .env files are not available
strBackendSupabaseUrl="https://qptddifkwfdyuhqhujul.supabase.co"
strBackendSupabaseKey="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFwdGRkaWZrd2ZkeXVocWh1anVsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDczNDUxNzIsImV4cCI6MjA2MjkyMTE3Mn0.roePCKt1WCX1bpDmOGMSL2XPTQGLO_9Kp9hfbbgP5ds"
strBackendDbUser="postgres.qptddifkwfdyuhqhujul"
strBackendDbPassword="PcXI4D0S4PMAEyKd"
strBackendDbHost="aws-0-ap-southeast-1.pooler.supabase.com"
strBackendDbPort="5432"
strBackendDbName="postgres"
strBackendGoogleAiApiKey="AIzaSyCY4b4mhpy-1fXkt4NF224JWsiPJio6b5Q"
strFrontendApiUrl="http://localhost:8000"
strFrontendSupabaseUrl="https://qptddifkwfdyuhqhujul.supabase.co"
strFrontendSupabaseKey="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFwdGRkaWZrd2ZkeXVocWh1anVsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDczNDUxNzIsImV4cCI6MjA2MjkyMTE3Mn0.roePCKt1WCX1bpDmOGMSL2XPTQGLO_9Kp9hfbbgP5ds"

strBackendDatabaseUrl="postgresql://${strBackendDbUser}:${strBackendDbPassword}@${strBackendDbHost}:${strBackendDbPort}/${strBackendDbName}"

# Create logs directory if it doesn't exist
if [[ ! -d "${LOG_DIR}" ]]; then
    mkdir -p "${LOG_DIR}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] [SETUP] Created logs directory" >> "${LOG_FILE}"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] [STARTUP] Suno container startup initiated" >> "${LOG_FILE}"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] [STARTUP] Log file: ${LOG_FILE}" >> "${LOG_FILE}"
echo "[CHECK] Log file: ${LOG_FILE}"
echo ""

# Function to log messages
log() {
    local level=$1
    local component=$2
    local message=$3
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] [${component}] ${message}" >> "${LOG_FILE}"
    echo "[${level}] ${message}"
}

# Docker availability check
log "INFO" "DOCKER-CHECK" "Checking Docker availability..."
if ! command -v docker &> /dev/null; then
    log "ERROR" "DOCKER-CHECK" "Docker is not installed or not in PATH"
    echo ""
    echo "[ERROR] Docker is not installed or not running!"
    echo ""
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    echo "After installation, ensure Docker Desktop is running and try again."
    echo ""
    exit 1
fi
DOCKER_VERSION=$(docker --version)
log "SUCCESS" "DOCKER-CHECK" "Docker available: ${DOCKER_VERSION}"

# Docker daemon check
log "INFO" "DOCKER-CHECK" "Checking Docker daemon status..."
if ! docker info &> /dev/null; then
    log "ERROR" "DOCKER-CHECK" "Docker daemon is not running"
    echo ""
    echo "[ERROR] Docker daemon is not running!"
    echo ""
    echo "Please start Docker Desktop and wait for it to fully initialize."
    echo ""
    exit 1
fi
log "SUCCESS" "DOCKER-CHECK" "Docker daemon is running"

# Port availability check
log "INFO" "PORT-CHECK" "Checking port availability..."
if lsof -Pi :3001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    log "WARNING" "PORT-CHECK" "Port 3001 is already in use"
    echo "[WARNING] Port 3001 is already in use. Frontend may not start properly."
fi
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    log "WARNING" "PORT-CHECK" "Port 8000 is already in use"
    echo "[WARNING] Port 8000 is already in use. Backend may not start properly."
fi
log "INFO" "PORT-CHECK" "Port check completed"

# Create required directories
log "INFO" "SETUP" "Creating required directories..."
[[ ! -d "${BASE_DIR}/songs" ]] && mkdir -p "${BASE_DIR}/songs" && log "INFO" "SETUP" "Created songs directory"
[[ ! -d "${BASE_DIR}/camoufox_session_data" ]] && mkdir -p "${BASE_DIR}/camoufox_session_data" && log "INFO" "SETUP" "Created camoufox_session_data directory"
[[ ! -d "${BASE_DIR}/container_health" ]] && mkdir -p "${BASE_DIR}/container_health" && log "INFO" "SETUP" "Created container_health directory"
log "SUCCESS" "SETUP" "All required directories verified/created"

# Process input parameters or use defaults
strFrontendImage="${1:-${SUNO_FRONTEND_IMAGE:-vnmw7/suno-frontend:latest}}"
strBackendImage="${2:-${SUNO_BACKEND_IMAGE:-vnmw7/suno-backend:latest}}"

if [[ "${1:-}" == "" ]] && [[ "${SUNO_FRONTEND_IMAGE:-}" == "" ]]; then
    log "INFO" "CONFIG" "Using default frontend image: vnmw7/suno-frontend:latest"
fi
if [[ "${2:-}" == "" ]] && [[ "${SUNO_BACKEND_IMAGE:-}" == "" ]]; then
    log "INFO" "CONFIG" "Using default backend image: vnmw7/suno-backend:latest"
fi

strFrontendName="suno-frontend-startup"
strBackendName="suno-backend-startup"

echo ""
echo "========================================"
echo "CONTAINER CONFIGURATION"
echo "========================================"
echo "Frontend:"
echo " - Image: ${strFrontendImage}"
echo " - Container: ${strFrontendName}"
echo " - Port: 3001 [host] -> 3000 [container]"
echo "Backend:"
echo " - Image: ${strBackendImage}"
echo " - Container: ${strBackendName}"
echo " - Port: 8000 [host] -> 8000 [container]"
echo "========================================"
echo ""

log "INFO" "CONFIG" "Frontend: ${strFrontendImage} on port 3001"
log "INFO" "CONFIG" "Backend: ${strBackendImage} on port 8000"

# Check if images exist locally
log "INFO" "IMAGE-CHECK" "Verifying Docker images exist locally..."
if ! docker images "${strFrontendImage}" --format "{{.Repository}}:{{.Tag}}" | grep -q "${strFrontendImage}"; then
    log "ERROR" "IMAGE-CHECK" "Frontend image ${strFrontendImage} not found locally"
    echo "[ERROR] Frontend image not found!"
    echo "Please run pull-images.sh first to download the required images."
    exit 1
fi
log "SUCCESS" "IMAGE-CHECK" "Frontend image found"

if ! docker images "${strBackendImage}" --format "{{.Repository}}:{{.Tag}}" | grep -q "${strBackendImage}"; then
    log "ERROR" "IMAGE-CHECK" "Backend image ${strBackendImage} not found locally"
    echo "[ERROR] Backend image not found!"
    echo "Please run pull-images.sh first to download the required images."
    exit 1
fi
log "SUCCESS" "IMAGE-CHECK" "Backend image found"

# Cleanup function
cleanup() {
    echo ""
    log "INFO" "SHUTDOWN" "Container shutdown initiated"
    echo "[ACTION] Stopping containers..."
    log "INFO" "SHUTDOWN" "Stopping frontend container..."
    docker stop "${strFrontendName}" >/dev/null 2>&1 || true
    log "INFO" "SHUTDOWN" "Stopping backend container..."
    docker stop "${strBackendName}" >/dev/null 2>&1 || true
    if [[ -n "${intFrontendLogPid:-}" ]]; then
        kill "${intFrontendLogPid}" >/dev/null 2>&1 || true
    fi
    if [[ -n "${intBackendLogPid:-}" ]]; then
        kill "${intBackendLogPid}" >/dev/null 2>&1 || true
    fi
    log "SUCCESS" "SHUTDOWN" "All containers stopped successfully"
    echo "[SUCCESS] Containers stopped successfully"
    echo "[INFO] Session logs saved to: ${LOG_FILE}"
    echo ""
    echo "========================================"
    echo "[INFO] Container session completed"
    echo "========================================"
    echo ""
}
trap cleanup EXIT INT TERM

# Stop and remove existing containers
log "INFO" "CLEANUP" "Stopping any existing containers..."
docker stop "${strFrontendName}" >/dev/null 2>&1 || true
docker stop "${strBackendName}" >/dev/null 2>&1 || true
docker rm -f "${strFrontendName}" >/dev/null 2>&1 || true
docker rm -f "${strBackendName}" >/dev/null 2>&1 || true
log "SUCCESS" "CLEANUP" "Cleanup completed"

echo ""
echo "========================================"
echo "STARTING CONTAINERS"
echo "========================================"
echo ""

# Default environment variables for backend (embedded for hassle-free usage)
BACKEND_ENV_VARS="-e PYTHONUNBUFFERED=1"
BACKEND_ENV_VARS="${BACKEND_ENV_VARS} -e LOG_LEVEL=DEBUG"
BACKEND_ENV_VARS="${BACKEND_ENV_VARS} -e SUPABASE_URL=${strBackendSupabaseUrl}"
BACKEND_ENV_VARS="${BACKEND_ENV_VARS} -e SUPABASE_KEY=${strBackendSupabaseKey}"
BACKEND_ENV_VARS="${BACKEND_ENV_VARS} -e DATABASE_URL=${strBackendDatabaseUrl}"
BACKEND_ENV_VARS="${BACKEND_ENV_VARS} -e USER=${strBackendDbUser}"
BACKEND_ENV_VARS="${BACKEND_ENV_VARS} -e PASSWORD=${strBackendDbPassword}"
BACKEND_ENV_VARS="${BACKEND_ENV_VARS} -e HOST=${strBackendDbHost}"
BACKEND_ENV_VARS="${BACKEND_ENV_VARS} -e PORT=${strBackendDbPort}"
BACKEND_ENV_VARS="${BACKEND_ENV_VARS} -e DBNAME=${strBackendDbName}"
BACKEND_ENV_VARS="${BACKEND_ENV_VARS} -e GOOGLE_AI_API_KEY=${strBackendGoogleAiApiKey}"

# Check if .env exists and load it if present
if [[ -f "${BASE_DIR}/backend/.env" ]]; then
    log "INFO" "ENV" "Found backend .env file, loading environment variables..."
    BACKEND_ENV_FILE="--env-file ${BASE_DIR}/backend/.env"
else
    log "INFO" "ENV" "No backend .env file found, using inline environment configuration"
    BACKEND_ENV_FILE=""
fi

# Start backend container with volumes, restart policy, and logging
log "INFO" "BACKEND" "Starting backend container..."
echo "[BACKEND] Starting container..."

BACKEND_CMD="docker run -d"
BACKEND_CMD="${BACKEND_CMD} --name ${strBackendName}"
BACKEND_CMD="${BACKEND_CMD} --restart unless-stopped"
BACKEND_CMD="${BACKEND_CMD} -p 8000:8000"
BACKEND_CMD="${BACKEND_CMD} ${BACKEND_ENV_VARS}"
BACKEND_CMD="${BACKEND_CMD} ${BACKEND_ENV_FILE}"
BACKEND_CMD="${BACKEND_CMD} -v ${BASE_DIR}/logs:/app/logs"
BACKEND_CMD="${BACKEND_CMD} -v ${BASE_DIR}/songs:/app/songs"
BACKEND_CMD="${BACKEND_CMD} -v ${BASE_DIR}/camoufox_session_data:/app/camoufox_session_data"
BACKEND_CMD="${BACKEND_CMD} ${strBackendImage}"

log "DEBUG" "BACKEND" "Executing: ${BACKEND_CMD}"
BACKEND_ID=$(eval ${BACKEND_CMD} 2>&1)

# Check if backend started successfully
if ! docker ps --filter "id=${BACKEND_ID}" --format "{{.ID}}" | grep -q "${BACKEND_ID:0:12}"; then
    log "ERROR" "BACKEND" "Failed to start backend container"
    echo "[ERROR] Backend container failed to start!"
    echo ""
    echo "Checking container logs for errors..."
    docker logs "${strBackendName}" 2>&1 | tail -20
    echo ""
    echo "Common issues:"
    echo "- Port 8000 already in use"
    echo "- Missing environment variables"
    echo "- Image corruption (try pull-images.sh again)"
    echo ""
    exit 1
fi
log "SUCCESS" "BACKEND" "Backend container started with ID: ${BACKEND_ID:0:12}"
echo "  → Container ID: ${BACKEND_ID:0:12}"
echo "  → Port: 8000"
echo "  → Logs: ${LOG_DIR}"
echo "  → Status: ✓ Running"

# Wait for backend to be healthy
log "INFO" "BACKEND" "Waiting for backend to be healthy..."
echo "  → Health check: Waiting..."
HEALTH_RETRIES=0
while [[ ${HEALTH_RETRIES} -lt 30 ]]; do
    if docker exec "${strBackendName}" python -c "import http.client; conn=http.client.HTTPConnection('127.0.0.1', 8000, timeout=5); conn.request('GET', '/'); print(conn.getresponse().status)" >/dev/null 2>&1; then
        log "SUCCESS" "BACKEND" "Backend is healthy and responding"
        echo "  → Health check: ✓ Healthy"
        break
    fi
    sleep 2
    ((HEALTH_RETRIES++))
done

if [[ ${HEALTH_RETRIES} -eq 30 ]]; then
    log "ERROR" "BACKEND" "Backend health check failed after 30 attempts"
    echo "  → Health check: ✗ Failed"
    echo ""
    echo "[ERROR] Backend container logs:"
    docker logs "${strBackendName}" --tail 50 2>&1
    docker logs "${strBackendName}" --tail 100 2>&1 > "${LOG_DIR}/backend_crash_${TIMESTAMP}.log"
    log "ERROR" "BACKEND" "Backend crash log saved to backend_crash_${TIMESTAMP}.log"
    exit 1
fi
echo ""

# Default environment variables for frontend (embedded for hassle-free usage)
FRONTEND_ENV_VARS="-e NODE_ENV=production"
FRONTEND_ENV_VARS="${FRONTEND_ENV_VARS} -e VITE_API_URL=${strFrontendApiUrl}"
FRONTEND_ENV_VARS="${FRONTEND_ENV_VARS} -e PORT=3000"
FRONTEND_ENV_VARS="${FRONTEND_ENV_VARS} -e HOST=0.0.0.0"
FRONTEND_ENV_VARS="${FRONTEND_ENV_VARS} -e VITE_SUPABASE_URL=${strFrontendSupabaseUrl}"
FRONTEND_ENV_VARS="${FRONTEND_ENV_VARS} -e VITE_SUPABASE_KEY=${strFrontendSupabaseKey}"

# Check if frontend .env exists
if [[ -f "${BASE_DIR}/frontend/.env" ]]; then
    log "INFO" "ENV" "Found frontend .env file, loading environment variables..."
    FRONTEND_ENV_FILE="--env-file ${BASE_DIR}/frontend/.env"
else
    log "INFO" "ENV" "No frontend .env file found, using inline environment configuration"
    FRONTEND_ENV_FILE=""
fi

# Start frontend container
log "INFO" "FRONTEND" "Starting frontend container..."
echo "[FRONTEND] Starting container..."

FRONTEND_CMD="docker run -d"
FRONTEND_CMD="${FRONTEND_CMD} --name ${strFrontendName}"
FRONTEND_CMD="${FRONTEND_CMD} --restart unless-stopped"
FRONTEND_CMD="${FRONTEND_CMD} -p 3001:3000"
FRONTEND_CMD="${FRONTEND_CMD} ${FRONTEND_ENV_VARS}"
FRONTEND_CMD="${FRONTEND_CMD} ${FRONTEND_ENV_FILE}"
FRONTEND_CMD="${FRONTEND_CMD} ${strFrontendImage}"

log "DEBUG" "FRONTEND" "Executing: ${FRONTEND_CMD}"
FRONTEND_ID=$(eval ${FRONTEND_CMD} 2>&1)

# Check if frontend started successfully
if ! docker ps --filter "id=${FRONTEND_ID}" --format "{{.ID}}" | grep -q "${FRONTEND_ID:0:12}"; then
    log "ERROR" "FRONTEND" "Failed to start frontend container"
    echo "[ERROR] Frontend container failed to start!"
    echo ""
    echo "Checking container logs for errors..."
    docker logs "${strFrontendName}" 2>&1 | tail -20
    echo ""
    exit 1
fi
log "SUCCESS" "FRONTEND" "Frontend container started with ID: ${FRONTEND_ID:0:12}"
echo "  → Container ID: ${FRONTEND_ID:0:12}"
echo "  → Port: 3001"
echo "  → Environment: Production"
echo "  → Status: ✓ Running"

# Wait for frontend to be healthy
log "INFO" "FRONTEND" "Waiting for frontend to be healthy..."
echo "  → Health check: Waiting..."
HEALTH_RETRIES=0
while [[ ${HEALTH_RETRIES} -lt 30 ]]; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:3001 | grep -q "200\|301\|302"; then
        log "SUCCESS" "FRONTEND" "Frontend is healthy and responding"
        echo "  → Health check: ✓ Healthy"
        break
    fi
    sleep 2
    ((HEALTH_RETRIES++))
done

if [[ ${HEALTH_RETRIES} -eq 30 ]]; then
    log "ERROR" "FRONTEND" "Frontend health check failed after 30 attempts"
    echo "  → Health check: ✗ Failed"
    echo ""
    echo "[ERROR] Frontend container logs:"
    docker logs "${strFrontendName}" --tail 50 2>&1
    docker logs "${strFrontendName}" --tail 100 2>&1 > "${LOG_DIR}/frontend_crash_${TIMESTAMP}.log"
    log "ERROR" "FRONTEND" "Frontend crash log saved to frontend_crash_${TIMESTAMP}.log"
    exit 1
fi

echo ""
echo "========================================"
echo "✓ ALL SERVICES STARTED SUCCESSFULLY"
echo "========================================"
echo "Frontend URL: http://localhost:3001"
echo "Backend URL: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Logs Directory: ${LOG_DIR}"
echo ""
echo "Container Status:"
docker ps --filter "name=suno" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo "========================================"
echo ""

log "SUCCESS" "STARTUP" "All containers started successfully"

# Start log streaming (save to files while displaying)
echo "[ACTION] Starting log monitoring..."
echo "[INFO] Container logs are being saved to:"
echo "  - Frontend: ${LOG_DIR}/frontend_${TIMESTAMP}.log"
echo "  - Backend: ${LOG_DIR}/backend_${TIMESTAMP}.log"
echo ""
echo "[INFO] Containers are running with auto-restart enabled."
echo "[INFO] They will automatically restart if they crash."
echo ""
echo "[INFO] Streaming logs. Press Ctrl+C to stop both containers."
echo ""

# Stream backend logs to file and console
docker logs "${strBackendName}" --follow --details --timestamps 2>&1 | tee -a "${LOG_DIR}/backend_${TIMESTAMP}.log" &
intBackendLogPid=$!

# Stream frontend logs to file and console
docker logs "${strFrontendName}" --follow --details --timestamps 2>&1 | tee -a "${LOG_DIR}/frontend_${TIMESTAMP}.log" &
intFrontendLogPid=$!

# Wait for interrupt
wait
