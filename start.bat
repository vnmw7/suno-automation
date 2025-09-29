@echo off
echo Starting Suno Automation...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Check for .env files
if not exist backend\.env (
    echo Creating backend .env from example...
    copy backend\.env.example backend\.env
    echo Please edit backend\.env with your configuration
    pause
)

if not exist frontend\.env (
    echo Creating frontend .env from example...
    copy frontend\.env.example frontend\.env
    echo Please edit frontend\.env with your configuration
    pause
)

REM Start services
echo Starting services...
docker-compose -f docker-compose.yml -f docker-compose.windows.yml up -d

if errorlevel 0 (
    echo.
    echo Services started successfully!
    echo.
    echo Frontend: http://localhost:3000
    echo Backend API: http://localhost:8000
    echo.
    echo To view logs: docker-compose logs -f
    echo To stop: docker-compose down
) else (
    echo Failed to start services
    pause
    exit /b 1
)

pause