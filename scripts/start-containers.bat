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

for %%I in ("%~dp0..") do set "BASE_DIR=%%~fI"

REM Capture original CLI arguments before calling helper subroutines (call resets %1/%2)
set "CLIFrontendImage=%~1"
set "CLIBackendImage=%~2"

REM Inline environment configuration with override support (no .env required)
set "strBackendSupabaseUrl=!SUPABASE_URL!"
if defined strBackendSupabaseUrl (
    set "strBackendSupabaseUrlSource=env:SUPABASE_URL"
) else (
    set "strBackendSupabaseUrl=https://qptddifkwfdyuhqhujul.supabase.co"
    set "strBackendSupabaseUrlSource=default"
)

set "strBackendSupabaseKey=!SUPABASE_KEY!"
if defined strBackendSupabaseKey (
    set "strBackendSupabaseKeySource=env:SUPABASE_KEY"
) else (
    set "strBackendSupabaseKey=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFwdGRkaWZrd2ZkeXVocWh1anVsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDczNDUxNzIsImV4cCI6MjA2MjkyMTE3Mn0.roePCKt1WCX1bpDmOGMSL2XPTQGLO_9Kp9hfbbgP5ds"
    set "strBackendSupabaseKeySource=default"
)

set "strBackendDbUser=!USER!"
if defined strBackendDbUser (
    set "strBackendDbUserSource=env:USER"
) else (
    set "strBackendDbUser=postgres.qptddifkwfdyuhqhujul"
    set "strBackendDbUserSource=default"
)

set "strBackendDbPassword=!PASSWORD!"
if defined strBackendDbPassword (
    set "strBackendDbPasswordSource=env:PASSWORD"
) else (
    set "strBackendDbPassword=PcXI4D0S4PMAEyKd"
    set "strBackendDbPasswordSource=default"
)

set "strBackendDbHost=!HOST!"
if defined strBackendDbHost (
    set "strBackendDbHostSource=env:HOST"
) else (
    set "strBackendDbHost=aws-0-ap-southeast-1.pooler.supabase.com"
    set "strBackendDbHostSource=default"
)

set "strBackendDbPort=!PORT!"
if defined strBackendDbPort (
    set "strBackendDbPortSource=env:PORT"
) else (
    set "strBackendDbPort=5432"
    set "strBackendDbPortSource=default"
)

set "strBackendDbName=!DBNAME!"
if defined strBackendDbName (
    set "strBackendDbNameSource=env:DBNAME"
) else (
    set "strBackendDbName=postgres"
    set "strBackendDbNameSource=default"
)

set "strBackendGoogleAiApiKey=!GOOGLE_AI_API_KEY!"
if defined strBackendGoogleAiApiKey (
    set "strBackendGoogleAiApiKeySource=env:GOOGLE_AI_API_KEY"
) else (
    set "strBackendGoogleAiApiKey=AIzaSyCY4b4mhpy-1fXkt4NF224JWsiPJio6b5Q"
    set "strBackendGoogleAiApiKeySource=default"
)

set "strFrontendApiUrl=!FRONTEND_API_URL!"
if not defined strFrontendApiUrl set "strFrontendApiUrl=!VITE_API_URL!"
if defined strFrontendApiUrl (
    if defined FRONTEND_API_URL (
        set "strFrontendApiUrlSource=env:FRONTEND_API_URL"
    ) else (
        set "strFrontendApiUrlSource=env:VITE_API_URL"
    )
) else (
    set "strFrontendApiUrl=http://localhost:8000"
    set "strFrontendApiUrlSource=default"
)

set "strFrontendSupabaseUrl=!VITE_SUPABASE_URL!"
if not defined strFrontendSupabaseUrl set "strFrontendSupabaseUrl=!SUPABASE_URL!"
if defined strFrontendSupabaseUrl (
    if defined VITE_SUPABASE_URL (
        set "strFrontendSupabaseUrlSource=env:VITE_SUPABASE_URL"
    ) else (
        set "strFrontendSupabaseUrlSource=env:SUPABASE_URL"
    )
) else (
    set "strFrontendSupabaseUrl=https://qptddifkwfdyuhqhujul.supabase.co"
    set "strFrontendSupabaseUrlSource=default"
)

set "strFrontendSupabaseKey=!VITE_SUPABASE_KEY!"
if not defined strFrontendSupabaseKey set "strFrontendSupabaseKey=!SUPABASE_KEY!"
if defined strFrontendSupabaseKey (
    if defined VITE_SUPABASE_KEY (
        set "strFrontendSupabaseKeySource=env:VITE_SUPABASE_KEY"
    ) else (
        set "strFrontendSupabaseKeySource=env:SUPABASE_KEY"
    )
) else (
    set "strFrontendSupabaseKey=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFwdGRkaWZrd2ZkeXVocWh1anVsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDczNDUxNzIsImV4cCI6MjA2MjkyMTE3Mn0.roePCKt1WCX1bpDmOGMSL2XPTQGLO_9Kp9hfbbgP5ds"
    set "strFrontendSupabaseKeySource=default"
)

set "strBackendDatabaseUrl=!DATABASE_URL!"
if defined strBackendDatabaseUrl (
    set "strBackendDatabaseUrlSource=env:DATABASE_URL"
) else (
    set "strBackendDatabaseUrl=postgresql://!strBackendDbUser!:!strBackendDbPassword!@!strBackendDbHost!:!strBackendDbPort!/!strBackendDbName!"
    set "strBackendDatabaseUrlSource=derived"
)

REM Set up logging
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,4%%dt:~4,2%%dt:~6,2%_%dt:~8,2%%dt:~10,2%%dt:~12,2%"
set "LOG_DIR=!BASE_DIR!\logs"
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

REM Ensure Browserforge datasets are available locally to avoid registry downloads
set "strBrowserforgeHeadersDir=!BASE_DIR!\backend\browserforge_data\headers"
set "strBrowserforgeFingerprintsDir=!BASE_DIR!\backend\browserforge_data\fingerprints"

if not exist "!strBrowserforgeHeadersDir!" (
    call :log "ERROR" "SETUP" "Missing browserforge headers dataset under backend\browserforge_data\headers"
    echo [ERROR] Browserforge headers dataset not found at: !strBrowserforgeHeadersDir!
    echo Please extract the dataset from apify_fingerprint_datapoints into backend\browserforge_data before retrying.
    pause
    exit /b 1
)
if not exist "!strBrowserforgeFingerprintsDir!" (
    call :log "ERROR" "SETUP" "Missing browserforge fingerprints dataset under backend\browserforge_data\fingerprints"
    echo [ERROR] Browserforge fingerprint dataset not found at: !strBrowserforgeFingerprintsDir!
    echo Please extract the dataset from apify_fingerprint_datapoints into backend\browserforge_data before retrying.
    pause
    exit /b 1
)
if not exist "!strBrowserforgeHeadersDir!\input-network.zip" (
    call :log "ERROR" "SETUP" "Browserforge headers dataset incomplete (input-network.zip missing)"
    echo [ERROR] Browserforge dataset incomplete: input-network.zip missing.
    pause
    exit /b 1
)
if not exist "!strBrowserforgeFingerprintsDir!\fingerprint-network.zip" (
    call :log "ERROR" "SETUP" "Browserforge fingerprint dataset incomplete (fingerprint-network.zip missing)"
    echo [ERROR] Browserforge dataset incomplete: fingerprint-network.zip missing.
    pause
    exit /b 1
)
call :log "INFO" "SETUP" "Browserforge datasets found locally; mounting into backend container."

REM Note configuration source without exposing secret values
if /I "!strBackendSupabaseUrlSource!"=="default" (
    call :log "WARNING" "CONFIG" "Backend Supabase URL using bundled default (override with SUPABASE_URL or backend\.env)."
) else (
    call :log "INFO" "CONFIG" "Backend Supabase URL sourced from !strBackendSupabaseUrlSource!"
)
if /I "!strBackendSupabaseKeySource!"=="default" (
    call :log "WARNING" "CONFIG" "Backend Supabase key using bundled default (override with SUPABASE_KEY or backend\.env)."
) else (
    call :log "INFO" "CONFIG" "Backend Supabase key sourced from !strBackendSupabaseKeySource!"
)
if /I "!strBackendDatabaseUrlSource!"=="derived" (
    call :log "INFO" "CONFIG" "Database URL constructed from bundled credentials."
) else if /I "!strBackendDatabaseUrlSource!"=="default" (
    call :log "WARNING" "CONFIG" "Database URL using bundled default value."
) else (
    call :log "INFO" "CONFIG" "Database URL sourced from !strBackendDatabaseUrlSource!"
)
if /I "!strBackendGoogleAiApiKeySource!"=="default" (
    call :log "WARNING" "CONFIG" "Google AI API key using bundled default."
) else (
    call :log "INFO" "CONFIG" "Google AI API key sourced from !strBackendGoogleAiApiKeySource!"
)
if /I "!strFrontendApiUrlSource!"=="default" (
    call :log "INFO" "CONFIG" "Frontend API URL using bundled default (http://localhost:8000)."
) else (
    call :log "INFO" "CONFIG" "Frontend API URL sourced from !strFrontendApiUrlSource!"
)
if /I "!strFrontendSupabaseKeySource!"=="default" (
    call :log "WARNING" "CONFIG" "Frontend Supabase key using bundled default."
) else (
    call :log "INFO" "CONFIG" "Frontend Supabase key sourced from !strFrontendSupabaseKeySource!"
)

REM Process input parameters or use defaults
set "strFrontendImage=!CLIFrontendImage!"
set "strBackendImage=!CLIBackendImage!"

if "!strFrontendImage!"=="" (
    set "strFrontendImage=vnmw7/suno-frontend:latest"
    call :log "INFO" "CONFIG" "Using default frontend image: vnmw7/suno-frontend:latest"
)
if "!strBackendImage!"=="" (
    set "strBackendImage=vnmw7/suno-backend-startup:latest"
    call :log "INFO" "CONFIG" "Using default backend image: vnmw7/suno-backend-startup:latest"
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
set "BACKEND_ENV_VARS=!BACKEND_ENV_VARS! -e SUPABASE_URL=!strBackendSupabaseUrl!"
set "BACKEND_ENV_VARS=!BACKEND_ENV_VARS! -e SUPABASE_KEY=!strBackendSupabaseKey!"
set "BACKEND_ENV_VARS=!BACKEND_ENV_VARS! -e DATABASE_URL=!strBackendDatabaseUrl!"
set "BACKEND_ENV_VARS=!BACKEND_ENV_VARS! -e USER=!strBackendDbUser!"
set "BACKEND_ENV_VARS=!BACKEND_ENV_VARS! -e PASSWORD=!strBackendDbPassword!"
set "BACKEND_ENV_VARS=!BACKEND_ENV_VARS! -e HOST=!strBackendDbHost!"
set "BACKEND_ENV_VARS=!BACKEND_ENV_VARS! -e PORT=!strBackendDbPort!"
set "BACKEND_ENV_VARS=!BACKEND_ENV_VARS! -e DBNAME=!strBackendDbName!"
set "BACKEND_ENV_VARS=!BACKEND_ENV_VARS! -e GOOGLE_AI_API_KEY=!strBackendGoogleAiApiKey!"

REM Check if .env exists and load it if present
if exist "!BASE_DIR!\backend\.env" (
    call :log "INFO" "ENV" "Found backend .env file, loading environment variables..."
    set "BACKEND_ENV_FILE=--env-file !BASE_DIR!\backend\.env"
) else (
    call :log "INFO" "ENV" "No backend .env file found, using inline environment configuration"
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
set "BACKEND_CMD=!BACKEND_CMD! --mount type=bind,src=""!BASE_DIR!\logs"",dst=/app/logs"
set "BACKEND_CMD=!BACKEND_CMD! --mount type=bind,src=""!BASE_DIR!\songs"",dst=/app/songs"
set "BACKEND_CMD=!BACKEND_CMD! --mount type=bind,src=""!BASE_DIR!\camoufox_session_data"",dst=/app/camoufox_session_data"
set "BACKEND_CMD=!BACKEND_CMD! --mount type=bind,src=""!strBrowserforgeHeadersDir!"",dst=/usr/local/lib/python3.11/site-packages/browserforge/headers/data"
set "BACKEND_CMD=!BACKEND_CMD! --mount type=bind,src=""!strBrowserforgeFingerprintsDir!"",dst=/usr/local/lib/python3.11/site-packages/browserforge/fingerprints/data"
set "BACKEND_CMD=!BACKEND_CMD! !strBackendImage!"

call :log "DEBUG" "BACKEND" "Executing docker run with inline environment and bind mounts."
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
echo   → Health check: Waiting for healthy status...
call :wait_for_health "!strBackendName!" 40
if errorlevel 3 goto backend_health_inspect_error
if errorlevel 2 goto backend_health_unhealthy
if errorlevel 1 goto backend_health_timeout
call :log "SUCCESS" "BACKEND" "Backend is healthy and responding"
echo   → Health check: ✓ Healthy
echo.

REM Default environment variables for frontend (embedded for hassle-free usage)
set "FRONTEND_ENV_VARS=-e NODE_ENV=production"
set "FRONTEND_ENV_VARS=!FRONTEND_ENV_VARS! -e VITE_API_URL=!strFrontendApiUrl!"
set "FRONTEND_ENV_VARS=!FRONTEND_ENV_VARS! -e BACKEND_URL=!strFrontendApiUrl!"
set "FRONTEND_ENV_VARS=!FRONTEND_ENV_VARS! -e PORT=3000"
set "FRONTEND_ENV_VARS=!FRONTEND_ENV_VARS! -e HOST=0.0.0.0"
set "FRONTEND_ENV_VARS=!FRONTEND_ENV_VARS! -e VITE_SUPABASE_URL=!strFrontendSupabaseUrl!"
set "FRONTEND_ENV_VARS=!FRONTEND_ENV_VARS! -e VITE_SUPABASE_KEY=!strFrontendSupabaseKey!"
set "FRONTEND_ENV_VARS=!FRONTEND_ENV_VARS! -e SUPABASE_URL=!strFrontendSupabaseUrl!"
set "FRONTEND_ENV_VARS=!FRONTEND_ENV_VARS! -e SUPABASE_KEY=!strFrontendSupabaseKey!"

REM Check if frontend .env exists
if exist "!BASE_DIR!\frontend\.env" (
    call :log "INFO" "ENV" "Found frontend .env file, loading environment variables..."
    set "FRONTEND_ENV_FILE=--env-file !BASE_DIR!\frontend\.env"
) else (
    call :log "INFO" "ENV" "No frontend .env file found, using inline environment configuration"
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

call :log "DEBUG" "FRONTEND" "Executing docker run for frontend container."
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
echo   → Health check: Waiting for healthy status...
call :wait_for_health "!strFrontendName!" 40
if errorlevel 3 goto frontend_health_inspect_error
if errorlevel 2 goto frontend_health_unhealthy
if errorlevel 1 goto frontend_health_timeout
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
echo.
echo Detailed Health:
docker inspect --format "{{.Name}}\t{{.State.Status}}\t{{if .State.Health}}{{.State.Health.Status}}{{end}}" "!strBackendName!"
docker inspect --format "{{.Name}}\t{{.State.Status}}\t{{if .State.Health}}{{.State.Health.Status}}{{end}}" "!strFrontendName!"
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

:wait_for_health
setlocal EnableDelayedExpansion
set "WFH_CONTAINER=%~1"
set "WFH_MAX_ATTEMPTS=%~2"
if not defined WFH_MAX_ATTEMPTS set "WFH_MAX_ATTEMPTS=30"
set /a WFH_ATTEMPT=0
set "WFH_LAST_STATUS="
:wait_for_health_loop
set "WFH_STATUS="
for /f "usebackq tokens=*" %%H in (`docker inspect --format="{{.State.Health.Status}}" "!WFH_CONTAINER!" 2^>^&1`) do (
    if not defined WFH_STATUS set "WFH_STATUS=%%~H"
)
if not defined WFH_STATUS (
    set "WFH_STATUS=pending"
)
if /I "!WFH_STATUS:~0,5!"=="Error" (
    endlocal & exit /b 3
)
if "!WFH_STATUS!" NEQ "!WFH_LAST_STATUS!" (
    call :log "INFO" "HEALTH" "Container %~1 status: !WFH_STATUS!"
    set "WFH_LAST_STATUS=!WFH_STATUS!"
)
if /I "!WFH_STATUS!"=="healthy" (
    endlocal & exit /b 0
)
if /I "!WFH_STATUS!"=="unhealthy" (
    endlocal & exit /b 2
)
if /I "!WFH_STATUS!"=="starting" (
    REM Continue waiting
) else if /I "!WFH_STATUS!"=="pending" (
    REM Continue waiting when status not yet available
) else if /I "!WFH_STATUS!"=="null" (
    REM Treat null as pending
) else (
    REM Unknown status signals continue but still subject to timeout
)
if !WFH_ATTEMPT! GEQ !WFH_MAX_ATTEMPTS! (
    endlocal & exit /b 1
)
timeout /t 2 >nul 2>&1
set /a WFH_ATTEMPT+=1
goto wait_for_health_loop

:backend_health_timeout
call :log "ERROR" "BACKEND" "Backend health check timed out before reaching healthy status"
echo   → Health check: ✗ Timed out
goto backend_logs_on_error

:backend_health_unhealthy
call :log "ERROR" "BACKEND" "Backend reported unhealthy status"
echo   → Health check: ✗ Unhealthy
goto backend_logs_on_error

:backend_health_inspect_error
call :log "ERROR" "BACKEND" "Failed to query backend health status via docker inspect"
echo   → Health check: ✗ Inspect error
goto backend_logs_on_error

:backend_logs_on_error
echo.
echo [ERROR] Backend container logs:
docker logs "!strBackendName!" --tail 50 2>&1
docker logs "!strBackendName!" --tail 100 2>&1 > "!LOG_DIR!\backend_crash_%TIMESTAMP%.log"
call :log "ERROR" "BACKEND" "Backend crash log saved to backend_crash_%TIMESTAMP%.log"
pause
exit /b 1

:frontend_health_timeout
call :log "ERROR" "FRONTEND" "Frontend health check timed out before reaching healthy status"
echo   → Health check: ✗ Timed out
goto frontend_logs_on_error

:frontend_health_unhealthy
call :log "ERROR" "FRONTEND" "Frontend reported unhealthy status"
echo   → Health check: ✗ Unhealthy
goto frontend_logs_on_error

:frontend_health_inspect_error
call :log "ERROR" "FRONTEND" "Failed to query frontend health status via docker inspect"
echo   → Health check: ✗ Inspect error
goto frontend_logs_on_error

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
