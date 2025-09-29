@echo off
echo ========================================
echo Suno Automation Frontend Installer
echo ========================================
echo.

REM Check for Docker
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not running.
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

echo Docker detected successfully!
echo.

REM Check for image tar file or build from source
if exist suno-frontend.tar (
    echo Loading Docker image from suno-frontend.tar...
    docker load -i suno-frontend.tar
    if errorlevel 1 (
        echo Failed to load Docker image!
        pause
        exit /b 1
    )
) else (
    echo Building Docker image from source...
    docker build -f Dockerfile.standalone -t suno-frontend:latest .
    if errorlevel 1 (
        echo Failed to build Docker image!
        pause
        exit /b 1
    )
)

echo.
echo Creating start script...

REM Create simplified start script
echo @echo off > start-suno-frontend.bat
echo echo Starting Suno Frontend... >> start-suno-frontend.bat
echo docker run -d --name suno-frontend -p 3001:3000 --restart unless-stopped suno-frontend:latest >> start-suno-frontend.bat
echo if errorlevel 0 ( >> start-suno-frontend.bat
echo     echo Frontend started at http://localhost:3001 >> start-suno-frontend.bat
echo ) >> start-suno-frontend.bat
echo pause >> start-suno-frontend.bat

REM Create stop script
echo @echo off > stop-suno-frontend.bat
echo echo Stopping Suno Frontend... >> stop-suno-frontend.bat
echo docker stop suno-frontend >> stop-suno-frontend.bat
echo docker rm suno-frontend >> stop-suno-frontend.bat
echo echo Frontend stopped. >> stop-suno-frontend.bat
echo pause >> stop-suno-frontend.bat

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Created:
echo - start-suno-frontend.bat (to start the frontend)
echo - stop-suno-frontend.bat (to stop the frontend)
echo.
echo To start the frontend, run: start-suno-frontend.bat
echo The frontend will be available at: http://localhost:3001
echo.
echo IMPORTANT: Make sure the backend is running at http://localhost:8000
echo.
pause