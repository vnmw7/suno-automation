@echo off
echo ========================================
echo Publish Suno Frontend to Docker Hub
echo ========================================
echo.

REM Get Docker Hub username
set /p DOCKER_USER=Enter your Docker Hub username:
set /p VERSION=Enter version tag (e.g., 1.0.0):

set IMAGE_NAME=%DOCKER_USER%/suno-frontend
set IMAGE_TAG=%VERSION%
set FULL_IMAGE=%IMAGE_NAME%:%IMAGE_TAG%
set LATEST_IMAGE=%IMAGE_NAME%:latest

echo.
echo Building image: %FULL_IMAGE%
docker build -f Dockerfile.standalone -t %FULL_IMAGE% -t %LATEST_IMAGE% .

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Logging in to Docker Hub...
docker login

if errorlevel 1 (
    echo Login failed!
    pause
    exit /b 1
)

echo.
echo Pushing %FULL_IMAGE%...
docker push %FULL_IMAGE%

echo Pushing %LATEST_IMAGE%...
docker push %LATEST_IMAGE%

if errorlevel 0 (
    echo.
    echo ========================================
    echo Successfully published to Docker Hub!
    echo ========================================
    echo.
    echo Users can now install with:
    echo   docker pull %FULL_IMAGE%
    echo   docker run -d -p 3001:3000 %FULL_IMAGE%
    echo.
    echo Or use docker-compose with:
    echo   image: %FULL_IMAGE%
) else (
    echo Push failed!
)

pause