@echo off
REM System: Suno Automation
REM Module: Docker Container Management
REM File URL: scripts/start-containers.bat
REM Purpose: Start Suno Automation containers with embedded configuration, robust logging, and automatic setup

title Suno Docker Container Manager

echo ========================================
echo SUNO AUTOMATION CONTAINER STARTUP
echo ========================================
echo.

setlocal EnableDelayedExpansion

REM Set up logging
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,4%%dt:~4,2%%dt:~6,2%_%dt:~8,2%%dt:~10,2%%dt:~12,2%"
set "LOG_DIR=%~dp0..\logs"
set "LOG_FILE=%LOG_DIR%\containers_%TIMESTAMP%.log"

REM Create logs directory if it doesn't exist
if not exist "!LOG_DIR!" (
    mkdir "!LOG_DIR!"
    echo [%date% %time%] [INFO] [SETUP] Created logs directory >> "!LOG_FILE!"
)

echo [%date% %time%] [INFO] [STARTUP] Suno container startup initiated >> "!LOG_FILE!"
echo [%date% %time%] [INFO] [STARTUP] Log file: !LOG_FILE! >> "!LOG_FILE!"
echo [CHECK] Log file: !LOG_FILE!
echo.

REM Function to log messages
goto :skip_functions
:log
    echo [%date% %time%] [%~1] [%~2] %~3 >> "!LOG_FILE!"
    echo [%~1] %~3
    goto :eof
:skip_functions

REM Docker availability check
call :log "INFO" "DOCKER-CHECK" "Checking Docker availability..."
docker --version >nul 2>&1
if errorlevel 1 (
    call :log "ERROR" "DOCKER-CHECK" "Docker is not installed or not in PATH"
    echo.
    echo [ERROR] Docker Desktop is not installed or not running!
    echo.
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    echo After installation, ensure Docker Desktop is running and try again.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('docker --version 2^>^&1') do set DOCKER_VERSION=%%i
call :log "SUCCESS" "DOCKER-CHECK" "Docker available: !DOCKER_VERSION!"

REM Docker daemon check
call :log "INFO" "DOCKER-CHECK" "Checking Docker daemon status..."
docker info >nul 2>&1
if errorlevel 1 (
    call :log "ERROR" "DOCKER-CHECK" "Docker daemon is not running"
    echo.
    echo [ERROR] Docker daemon is not running!
    echo.
    echo Please start Docker Desktop and wait for it to fully initialize.
    echo Look for the Docker whale icon in your system tray.
    echo.
    pause
    exit /b 1
)
call :log "SUCCESS" "DOCKER-CHECK" "Docker daemon is running"

REM Port availability check
call :log "INFO" "PORT-CHECK" "Checking port availability..."
netstat -an | findstr :3001 | findstr LISTENING >nul 2>&1
if not errorlevel 1 (
    call :log "WARNING" "PORT-CHECK" "Port 3001 is already in use"
    echo [WARNING] Port 3001 is already in use. Frontend may not start properly.
)
netstat -an | findstr :8000 | findstr LISTENING >nul 2>&1
if not errorlevel 1 (
    call :log "WARNING" "PORT-CHECK" "Port 8000 is already in use"
    echo [WARNING] Port 8000 is already in use. Backend may not start properly.
)
call :log "INFO" "PORT-CHECK" "Port check completed"

REM Create required directories
call :log "INFO" "SETUP" "Creating required directories..."
set "BASE_DIR=%~dp0.."
if not exist "!BASE_DIR!\songs" (
    mkdir "!BASE_DIR!\songs"
    call :log "INFO" "SETUP" "Created songs directory"
)
if not exist "!BASE_DIR!\camoufox_session_data" (
    mkdir "!BASE_DIR!\camoufox_session_data"
    call :log "INFO" "SETUP" "Created camoufox_session_data directory"
)
if not exist "!BASE_DIR!\container_health" (
    mkdir "!BASE_DIR!\container_health"
    call :log "INFO" "SETUP" "Created container_health directory"
)
call :log "SUCCESS" "SETUP" "All required directories verified/created"

REM Process input parameters or use defaults
set "strFrontendImage=%~1"
set "strBackendImage=%~2"

if "!strFrontendImage!"=="" (
    set "strFrontendImage=vnmw7/suno-frontend:latest"
    call :log "INFO" "CONFIG" "Using default frontend image: vnmw7/suno-frontend:latest"
)
if "!strBackendImage!"=="" (
    set "strBackendImage=vnmw7/suno-backend:latest"
    call :log "INFO" "CONFIG" "Using default backend image: vnmw7/suno-backend:latest"
)

set "strFrontendName=suno-frontend-startup"
set "strBackendName=suno-backend-startup"

echo.
echo ========================================
echo CONTAINER CONFIGURATION
echo ========================================
echo Frontend:
echo  - Image: !strFrontendImage!
echo  - Container: !strFrontendName!
echo  - Port: 3001 [host] -^> 3000 [container]
echo Backend:
echo  - Image: !strBackendImage!
echo  - Container: !strBackendName!
echo  - Port: 8000 [host] -^> 8000 [container]
echo ========================================
echo.

call :log "INFO" "CONFIG" "Frontend: !strFrontendImage! on port 3001"
call :log "INFO" "CONFIG" "Backend: !strBackendImage! on port 8000"

REM Check if images exist locally
call :log "INFO" "IMAGE-CHECK" "Verifying Docker images exist locally..."
docker images "!strFrontendImage!" --format "table {{.Repository}}:{{.Tag}}" | findstr /C:"!strFrontendImage!" >nul 2>&1
if errorlevel 1 (
    call :log "ERROR" "IMAGE-CHECK" "Frontend image !strFrontendImage! not found locally"
    echo [ERROR] Frontend image not found!
    echo Please run pull-images.bat first to download the required images.
    pause
    exit /b 1
)
call :log "SUCCESS" "IMAGE-CHECK" "Frontend image found"

docker images "!strBackendImage!" --format "table {{.Repository}}:{{.Tag}}" | findstr /C:"!strBackendImage!" >nul 2>&1
if errorlevel 1 (
    call :log "ERROR" "IMAGE-CHECK" "Backend image !strBackendImage! not found locally"
    echo [ERROR] Backend image not found!
    echo Please run pull-images.bat first to download the required images.
    pause
    exit /b 1
)
call :log "SUCCESS" "IMAGE-CHECK" "Backend image found"

REM Stop and remove existing containers
call :log "INFO" "CLEANUP" "Stopping any existing containers..."
docker stop "!strFrontendName!" >nul 2>&1
docker stop "!strBackendName!" >nul 2>&1
docker rm -f "!strFrontendName!" >nul 2>&1
docker rm -f "!strBackendName!" >nul 2>&1
call :log "SUCCESS" "CLEANUP" "Cleanup completed"

echo.
echo ========================================
echo STARTING CONTAINERS
echo ========================================
echo.

REM Default environment variables for backend (embedded for hassle-free usage)
set "BACKEND_ENV_VARS=-e PYTHONUNBUFFERED=1"
set "BACKEND_ENV_VARS=!BACKEND_ENV_VARS! -e LOG_LEVEL=DEBUG"
set "BACKEND_ENV_VARS=!BACKEND_ENV_VARS! -e PORT=8000"
set "BACKEND_ENV_VARS=!BACKEND_ENV_VARS! -e HOST=0.0.0.0"
set "BACKEND_ENV_VARS=!BACKEND_ENV_VARS! -e SUPABASE_URL=https://placeholder.supabase.co"
set "BACKEND_ENV_VARS=!BACKEND_ENV_VARS! -e SUPABASE_KEY=placeholder-key"
set "BACKEND_ENV_VARS=!BACKEND_ENV_VARS! -e DATABASE_URL=postgresql://user:pass@localhost/db"

REM Check if .env exists and load it if present
if exist "!BASE_DIR!\backend\.env" (
    call :log "INFO" "ENV" "Found backend .env file, loading environment variables..."
    set "BACKEND_ENV_FILE=--env-file !BASE_DIR!\backend\.env"
) else (
    call :log "WARNING" "ENV" "No backend .env file found, using embedded defaults"
    set "BACKEND_ENV_FILE="
)

REM Start backend container with volumes, restart policy, and logging
call :log "INFO" "BACKEND" "Starting backend container..."
echo [BACKEND] Starting container...

set "BACKEND_CMD=docker run -d"
set "BACKEND_CMD=!BACKEND_CMD! --name !strBackendName!"
set "BACKEND_CMD=!BACKEND_CMD! --restart unless-stopped"
set "BACKEND_CMD=!BACKEND_CMD! -p 8000:8000"
set "BACKEND_CMD=!BACKEND_CMD! !BACKEND_ENV_VARS!"
set "BACKEND_CMD=!BACKEND_CMD! !BACKEND_ENV_FILE!"
set "BACKEND_CMD=!BACKEND_CMD! -v !BASE_DIR!\logs:/app/logs"
set "BACKEND_CMD=!BACKEND_CMD! -v !BASE_DIR!\songs:/app/songs"
set "BACKEND_CMD=!BACKEND_CMD! -v !BASE_DIR!\camoufox_session_data:/app/camoufox_session_data"
set "BACKEND_CMD=!BACKEND_CMD! !strBackendImage!"

call :log "DEBUG" "BACKEND" "Executing: !BACKEND_CMD!"
for /f "tokens=*" %%i in ('!BACKEND_CMD! 2^>^&1') do set BACKEND_ID=%%i

REM Check if backend started successfully
docker ps --filter "id=!BACKEND_ID!" --format "table {{.ID}}" | findstr "!BACKEND_ID:~0,12!" >nul 2>&1
if errorlevel 1 (
    call :log "ERROR" "BACKEND" "Failed to start backend container"
    echo [ERROR] Backend container failed to start!
    echo.
    echo Checking container logs for errors...
    docker logs "!strBackendName!" --tail 20 2>&1
    echo.
    echo Common issues:
    echo - Port 8000 already in use
    echo - Missing environment variables
    echo - Image corruption (try pull-images.bat again)
    echo.
    pause
    exit /b 1
)
call :log "SUCCESS" "BACKEND" "Backend container started with ID: !BACKEND_ID:~0,12!"
echo   → Container ID: !BACKEND_ID:~0,12!
echo   → Port: 8000
echo   → Logs: !LOG_DIR!
echo   → Status: ✓ Running

REM Wait for backend to be healthy
call :log "INFO" "BACKEND" "Waiting for backend to be healthy..."
echo   → Health check: Waiting...
set "HEALTH_RETRIES=0"
:backend_health_loop
if !HEALTH_RETRIES! GEQ 30 (
    call :log "ERROR" "BACKEND" "Backend health check failed after 30 attempts"
    echo   → Health check: ✗ Failed
    goto backend_logs_on_error
)
timeout /t 2 >nul 2>&1
docker exec "!strBackendName!" python -c "import http.client; conn=http.client.HTTPConnection('127.0.0.1', 8000, timeout=5); conn.request('GET', '/'); print(conn.getresponse().status)" >nul 2>&1
if errorlevel 1 (
    set /a HEALTH_RETRIES+=1
    goto backend_health_loop
)
call :log "SUCCESS" "BACKEND" "Backend is healthy and responding"
echo   → Health check: ✓ Healthy
echo.

REM Default environment variables for frontend (embedded for hassle-free usage)
set "FRONTEND_ENV_VARS=-e NODE_ENV=production"
set "FRONTEND_ENV_VARS=!FRONTEND_ENV_VARS! -e VITE_API_URL=http://localhost:8000"
set "FRONTEND_ENV_VARS=!FRONTEND_ENV_VARS! -e PORT=3000"
set "FRONTEND_ENV_VARS=!FRONTEND_ENV_VARS! -e HOST=0.0.0.0"
set "FRONTEND_ENV_VARS=!FRONTEND_ENV_VARS! -e VITE_SUPABASE_URL=https://placeholder.supabase.co"
set "FRONTEND_ENV_VARS=!FRONTEND_ENV_VARS! -e VITE_SUPABASE_KEY=placeholder-key"

REM Check if frontend .env exists
if exist "!BASE_DIR!\frontend\.env" (
    call :log "INFO" "ENV" "Found frontend .env file, loading environment variables..."
    set "FRONTEND_ENV_FILE=--env-file !BASE_DIR!\frontend\.env"
) else (
    call :log "WARNING" "ENV" "No frontend .env file found, using embedded defaults"
    set "FRONTEND_ENV_FILE="
)

REM Start frontend container
call :log "INFO" "FRONTEND" "Starting frontend container..."
echo [FRONTEND] Starting container...

set "FRONTEND_CMD=docker run -d"
set "FRONTEND_CMD=!FRONTEND_CMD! --name !strFrontendName!"
set "FRONTEND_CMD=!FRONTEND_CMD! --restart unless-stopped"
set "FRONTEND_CMD=!FRONTEND_CMD! -p 3001:3000"
set "FRONTEND_CMD=!FRONTEND_CMD! !FRONTEND_ENV_VARS!"
set "FRONTEND_CMD=!FRONTEND_CMD! !FRONTEND_ENV_FILE!"
set "FRONTEND_CMD=!FRONTEND_CMD! !strFrontendImage!"

call :log "DEBUG" "FRONTEND" "Executing: !FRONTEND_CMD!"
for /f "tokens=*" %%i in ('!FRONTEND_CMD! 2^>^&1') do set FRONTEND_ID=%%i

REM Check if frontend started successfully
docker ps --filter "id=!FRONTEND_ID!" --format "table {{.ID}}" | findstr "!FRONTEND_ID:~0,12!" >nul 2>&1
if errorlevel 1 (
    call :log "ERROR" "FRONTEND" "Failed to start frontend container"
    echo [ERROR] Frontend container failed to start!
    echo.
    echo Checking container logs for errors...
    docker logs "!strFrontendName!" --tail 20 2>&1
    echo.
    pause
    exit /b 1
)
call :log "SUCCESS" "FRONTEND" "Frontend container started with ID: !FRONTEND_ID:~0,12!"
echo   → Container ID: !FRONTEND_ID:~0,12!
echo   → Port: 3001
echo   → Environment: Production
echo   → Status: ✓ Running

REM Wait for frontend to be healthy
call :log "INFO" "FRONTEND" "Waiting for frontend to be healthy..."
echo   → Health check: Waiting...
set "HEALTH_RETRIES=0"
:frontend_health_loop
if !HEALTH_RETRIES! GEQ 30 (
    call :log "ERROR" "FRONTEND" "Frontend health check failed after 30 attempts"
    echo   → Health check: ✗ Failed
    goto frontend_logs_on_error
)
timeout /t 2 >nul 2>&1
powershell -Command "(Invoke-WebRequest -Uri 'http://localhost:3001' -UseBasicParsing -TimeoutSec 5).StatusCode" >nul 2>&1
if errorlevel 1 (
    set /a HEALTH_RETRIES+=1
    goto frontend_health_loop
)
call :log "SUCCESS" "FRONTEND" "Frontend is healthy and responding"
echo   → Health check: ✓ Healthy

echo.
echo ========================================
echo ✓ ALL SERVICES STARTED SUCCESSFULLY
echo ========================================
echo Frontend URL: http://localhost:3001
echo Backend URL: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Logs Directory: !LOG_DIR!
echo.
echo Container Status:
docker ps --filter "name=suno" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ========================================
echo.

call :log "SUCCESS" "STARTUP" "All containers started successfully"

REM Start log streaming in new windows
echo [ACTION] Opening log windows for monitoring...
start "Frontend Logs - !strFrontendName!" cmd /c "title Frontend Logs && docker logs !strFrontendName! --follow --details --timestamps 2>&1"
start "Backend Logs - !strBackendName!" cmd /c "title Backend Logs && docker logs !strBackendName! --follow --details --timestamps 2>&1"

REM Also save logs to files in background
start /b cmd /c "docker logs !strFrontendName! --follow --details --timestamps >> !LOG_DIR!\frontend_%TIMESTAMP%.log 2>&1"
start /b cmd /c "docker logs !strBackendName! --follow --details --timestamps >> !LOG_DIR!\backend_%TIMESTAMP%.log 2>&1"

echo [INFO] Log windows opened. Container logs are being saved to:
echo   - Frontend: !LOG_DIR!\frontend_%TIMESTAMP%.log
echo   - Backend: !LOG_DIR!\backend_%TIMESTAMP%.log
echo.
echo [INFO] Containers are running with auto-restart enabled.
echo [INFO] They will automatically restart if they crash.
echo.
echo Press any key to stop both containers...
pause >nul

call :log "INFO" "SHUTDOWN" "User requested container shutdown"

echo.
echo [ACTION] Stopping containers...
call :log "INFO" "SHUTDOWN" "Stopping frontend container..."
docker stop "!strFrontendName!" >nul 2>&1
call :log "INFO" "SHUTDOWN" "Stopping backend container..."
docker stop "!strBackendName!" >nul 2>&1
call :log "SUCCESS" "SHUTDOWN" "All containers stopped successfully"

echo [SUCCESS] Containers stopped successfully
echo [INFO] Session logs saved to: !LOG_FILE!
goto end

:backend_logs_on_error
echo.
echo [ERROR] Backend container logs:
docker logs "!strBackendName!" --tail 50 2>&1
docker logs "!strBackendName!" --tail 100 2>&1 > "!LOG_DIR!\backend_crash_%TIMESTAMP%.log"
call :log "ERROR" "BACKEND" "Backend crash log saved to backend_crash_%TIMESTAMP%.log"
pause
exit /b 1

:frontend_logs_on_error
echo.
echo [ERROR] Frontend container logs:
docker logs "!strFrontendName!" --tail 50 2>&1
docker logs "!strFrontendName!" --tail 100 2>&1 > "!LOG_DIR!\frontend_crash_%TIMESTAMP%.log"
call :log "ERROR" "FRONTEND" "Frontend crash log saved to frontend_crash_%TIMESTAMP%.log"
pause
exit /b 1

:end
echo.
echo ========================================
echo [INFO] Container session completed
echo ========================================
echo.
pause