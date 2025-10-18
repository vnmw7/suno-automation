@echo off
REM System: Suno Automation
REM Module: Local Backend Startup
REM File URL: scripts/start-backend-local.bat
REM Purpose: Start backend locally as a workaround for Docker browserforge issues

title Suno Backend (Local)

echo ========================================
echo SUNO BACKEND LOCAL STARTUP
echo ========================================
echo.

cd backend

REM Check if virtual environment exists
if not exist ".venv" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
)

echo [INFO] Activating virtual environment...
call .venv\Scripts\activate

echo [INFO] Installing dependencies...
pip install -r requirements.txt

REM Set environment variables
set SUPABASE_URL=https://qptddifkwfdyuhqhujul.supabase.co
set SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFwdGRkaWZrd2ZkeXVocWh1anVsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDczNDUxNzIsImV4cCI6MjA2MjkyMTE3Mn0.roePCKt1WCX1bpDmOGMSL2XPTQGLO_9Kp9hfbbgP5ds
set DATABASE_URL=postgresql://postgres.qptddifkwfdyuhqhujul:PcXI4D0S4PMAEyKd@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
set USER=postgres.qptddifkwfdyuhqhujul
set PASSWORD=PcXI4D0S4PMAEyKd
set HOST=aws-0-ap-southeast-1.pooler.supabase.com
set PORT=5432
set DBNAME=postgres
set GOOGLE_AI_API_KEY=AIzaSyCY4b4mhpy-1fXkt4NF224JWsiPJio6b5Q

echo.
echo [INFO] Starting backend server...
echo [INFO] Backend will be available at: http://localhost:8000
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload