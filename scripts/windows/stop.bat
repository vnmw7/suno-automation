@echo off
REM System: Suno Automation
REM Module: Windows Stop Script
REM File URL: scripts/windows/stop.bat
REM Purpose: Stop the Suno Automation application on Windows

SetLocal EnableExtensions EnableDelayedExpansion

REM Display header
echo.
echo ========================================
echo  Suno Automation - Stop Script
echo ========================================
echo.
echo This script will stop the Suno Automation application.
echo.

REM Stop backend server
echo [INFO] Stopping backend server...
taskkill /f /im python.exe /fi "WINDOWTITLE eq Backend Server*" >nul 2>&1
if %errorLevel% equ 0 (
    echo [SUCCESS] Backend server stopped.
) else (
    echo [INFO] Backend server was not running or could not be stopped.
)

REM Stop frontend server
echo [INFO] Stopping frontend server...
taskkill /f /im node.exe /fi "WINDOWTITLE eq Frontend Server*" >nul 2>&1
if %errorLevel% equ 0 (
    echo [SUCCESS] Frontend server stopped.
) else (
    echo [INFO] Frontend server was not running or could not be stopped.
)

REM Alternative method: Kill by port
echo [INFO] Checking for processes on ports 8000 and 5173...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    echo [INFO] Killing process %%a on port 8000...
    taskkill /f /pid %%a >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -aon ^| find ":5173" ^| find "LISTENING"') do (
    echo [INFO] Killing process %%a on port 5173...
    taskkill /f /pid %%a >nul 2>&1
)

echo.
echo [SUCCESS] Suno Automation application has been stopped.
echo.
echo Press any key to exit...
pause >nul
exit /b 0