@echo off
REM System: Suno Automation
REM Module: Docker Image Setup
REM File URL: scripts/pull-images.bat
REM Purpose: Pull Suno Automation frontend and backend Docker images for a chosen registry and tag.

setlocal EnableDelayedExpansion

set "strRegistry=%~1"
set "strTag=%~2"

if "!strRegistry!"=="" (
    set /p strRegistry=Enter registry (for example, your-namespace): 
)
if "!strRegistry!"=="" (
    echo Registry is required. Exiting.
    goto end
)

if "!strTag!"=="" (
    set /p strTag=Enter tag [latest]: 
    if "!strTag!"=="" set "strTag=latest"
)

echo Pulling frontend image "!strRegistry!/suno-frontend:!strTag!"...
docker pull "!strRegistry!/suno-frontend:!strTag!"
if errorlevel 1 goto error

echo Pulling backend image "!strRegistry!/suno-backend:!strTag!"...
docker pull "!strRegistry!/suno-backend:!strTag!"
if errorlevel 1 goto error

echo Both images pulled successfully.
goto end

:error
echo Docker pull failed. Review the output above for details.

:end
pause
