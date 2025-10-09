@echo off
echo Starting Frontend Only (Docker)...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Check for .env file
if not exist .env (
    if exist .env.docker (
        echo Using .env.docker as environment file...
        copy .env.docker .env
    ) else if exist .env.example (
        echo Creating .env from .env.example...
        copy .env.example .env
        echo Please edit .env with your configuration
        pause
    )
)

REM Stop any existing frontend container
echo Stopping any existing frontend container...
docker-compose -f docker-compose.frontend.yml down 2>nul

REM Build and start frontend
echo Building frontend image...
docker-compose -f docker-compose.frontend.yml build

echo Starting frontend container...
docker-compose -f docker-compose.frontend.yml up -d

if errorlevel 0 (
    echo.
    echo Frontend started successfully!
    echo.
    echo Access the application at: http://localhost:3001
    echo.
    echo Make sure the backend is running at: http://localhost:8000
    echo.
    echo To view logs: docker-compose -f docker-compose.frontend.yml logs -f
    echo To stop: docker-compose -f docker-compose.frontend.yml down
) else (
    echo Failed to start frontend
    pause
    exit /b 1
)

pause