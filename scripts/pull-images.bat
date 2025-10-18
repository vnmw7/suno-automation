@echo off
REM System: Suno Automation
REM Module: Docker Image Setup
REM File URL: scripts/pull-images.bat
REM Purpose: Pull Suno Automation frontend and backend Docker images for a chosen registry and tag.

title Suno Docker Pull Images

echo ========================================
echo Suno Docker Pull Images Script
echo ========================================
echo.
echo [DEBUG] Script started at %date% %time%
echo.

setlocal EnableDelayedExpansion

echo [DEBUG] Checking Docker availability...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH
    echo Please install Docker Desktop and ensure it's running
    goto error
)
echo [SUCCESS] Docker is available
echo.

echo [DEBUG] Processing input parameters...
set "strRegistry=%~1"
set "strTag=%~2"
echo [DEBUG] Input registry: !strRegistry!
echo [DEBUG] Input tag: !strTag!
echo.

REM Automatically set defaults - no prompts for easy double-click usage
if "!strRegistry!"=="" (
    set "strRegistry=vnmw7"
    echo [INFO] No registry provided - using default: vnmw7
)
echo [DEBUG] Using registry: !strRegistry!
echo.

if "!strTag!"=="" (
    set "strTag=latest"
    echo [INFO] No tag provided - using default: latest
)
echo [DEBUG] Using tag: !strTag!
echo.

echo ========================================
echo AUTOMATIC PULL MODE
echo ========================================
echo Target Images:
echo  - !strRegistry!/suno-frontend:!strTag!
echo  - !strRegistry!/suno-backend-startup:!strTag!
echo ========================================
echo.

echo ========================================
echo Starting Docker pulls...
echo ========================================
echo.

echo [ACTION] Pulling frontend image "!strRegistry!/suno-frontend:!strTag!"...
echo [DEBUG] Executing: docker pull "!strRegistry!/suno-frontend:!strTag!"
docker pull "!strRegistry!/suno-frontend:!strTag!"
if errorlevel 1 (
    echo [ERROR] Failed to pull frontend image
    goto error
)
echo [SUCCESS] Frontend image pulled successfully
echo.

echo [ACTION] Pulling backend image "!strRegistry!/suno-backend-startup:!strTag!"...
echo [DEBUG] Executing: docker pull "!strRegistry!/suno-backend-startup:!strTag!"
docker pull "!strRegistry!/suno-backend-startup:!strTag!"
if errorlevel 1 (
    echo [ERROR] Failed to pull backend image
    goto error
)
echo [SUCCESS] Backend image pulled successfully
echo.

echo ========================================
echo [SUCCESS] Both images pulled successfully!
echo ========================================
echo [DEBUG] Script completed at %date% %time%
goto end

:error
echo.
echo ========================================
echo [ERROR] Docker pull operation failed
echo ========================================
echo Please review the output above for details.
echo Common issues:
echo - Docker Desktop not running
echo - Invalid registry name
echo - Network connectivity issues
echo - Authentication required for private registry

:end
echo.
pause
