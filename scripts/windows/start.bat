@echo off
REM System: Suno Automation
REM Module: Windows Start Script
REM File URL: scripts/windows/start.bat
REM Purpose: Start the Suno Automation application on Windows

SetLocal EnableExtensions EnableDelayedExpansion

REM Initialize variables
set "strScriptRoot=%~dp0"
set "strProjectRoot=%strScriptRoot%..\..\"
set "blnSuccess=1"

REM Display header
echo.
echo ========================================
echo  Suno Automation - Start Script
echo ========================================
echo.
echo This script will start the Suno Automation application.
echo.

REM Check if backend and frontend directories exist
if not exist "%strProjectRoot%backend" (
    echo [ERROR] Backend directory not found at: %strProjectRoot%backend
    echo Please ensure you have run the setup script first.
    set "blnSuccess=0"
    goto :displayFinalStatus
)

if not exist "%strProjectRoot%frontend" (
    echo [ERROR] Frontend directory not found at: %strProjectRoot%frontend
    echo Please ensure you have run the setup script first.
    set "blnSuccess=0"
    goto :displayFinalStatus
)

REM Check if backend virtual environment exists
if not exist "%strProjectRoot%backend\.venv" (
    echo [ERROR] Backend virtual environment not found.
    echo Please ensure you have run the setup script first.
    set "blnSuccess=0"
    goto :displayFinalStatus
)

REM Check if frontend node_modules exists
if not exist "%strProjectRoot%frontend\node_modules" (
    echo [ERROR] Frontend dependencies not installed.
    echo Please ensure you have run the setup script first.
    set "blnSuccess=0"
    goto :displayFinalStatus
)

REM Start backend server
echo [INFO] Starting backend server...
cd /d "%strProjectRoot%backend"
call .venv\Scripts\activate
start "Backend Server" cmd /k "python main.py"
call deactivate

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend server
echo [INFO] Starting frontend server...
cd /d "%strProjectRoot%frontend"
start "Frontend Server" cmd /k "npm run dev"

REM Display final status
:displayFinalStatus
echo.
echo ========================================
echo  Startup Complete
echo ========================================
echo.

if %blnSuccess% equ 1 (
    echo [SUCCESS] Suno Automation application is starting...
    echo.
    echo Backend server: http://localhost:8000
    echo Frontend server: http://localhost:5173
    echo.
    echo Two command windows have been opened for the backend and frontend servers.
    echo You can close this window now.
    echo.
    echo To stop the application, close the backend and frontend server windows,
    echo or run the stop.bat script.
) else (
    echo [ERROR] Failed to start the application.
    echo Please resolve the issues above and try again.
)

echo.
echo Press any key to exit...
pause >nul
exit /b %blnSuccess%