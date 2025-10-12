@echo off
REM System: Suno Automation
REM Module: Docker Image Setup
REM File URL: scripts/start-containers.bat
REM Purpose: Start Suno Automation frontend and backend containers and stream their logs.

setlocal EnableDelayedExpansion

set "strFrontendImage=%~1"
set "strBackendImage=%~2"

if "!strFrontendImage!"=="" set "strFrontendImage=suno-frontend:latest"
if "!strBackendImage!"=="" set "strBackendImage=suno-backend:latest"

set "strFrontendName=suno-frontend-startup"
set "strBackendName=suno-backend-startup"

echo Stopping any existing containers with names "!strFrontendName!" and "!strBackendName!"...
docker rm -f "!strFrontendName!" >nul 2>&1
docker rm -f "!strBackendName!" >nul 2>&1

echo Starting frontend container "!strFrontendImage!"...
docker run --rm -d --name "!strFrontendName!" -p 3001:3000 "!strFrontendImage!"
if errorlevel 1 goto error

echo Starting backend container "!strBackendImage!"...
docker run --rm -d --name "!strBackendName!" -p 8000:8000 "!strBackendImage!"
if errorlevel 1 goto error

echo Opening log windows (close them or press any key here to stop the containers)...
start "Frontend Logs" pwsh -NoProfile -Command "docker logs !strFrontendName! --follow --details --timestamps"
start "Backend Logs" pwsh -NoProfile -Command "docker logs !strBackendName! --follow --details --timestamps"

echo.
echo Containers are running. Press any key to stop both services.
pause >nul

echo Stopping containers...
docker stop "!strFrontendName!" >nul 2>&1
docker stop "!strBackendName!" >nul 2>&1
echo Done.
goto end

:error
echo Failed to start one of the containers. Review the Docker output above.

:end
