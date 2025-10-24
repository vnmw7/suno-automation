@echo off
REM System: Suno Automation
REM Module: Windows Setup Automation (No Admin Required)
REM File URL: setup-windows-no-admin.bat
REM Purpose: Setup script that doesn't require admin if tools are already installed

SetLocal EnableExtensions EnableDelayedExpansion

REM Initialize variables
set "strRepoUrl=https://github.com/vnmw7/suno-automation.git"
set "strRepoName=suno-automation"
set "strScriptRoot=%~dp0"
set "blnSuccess=1"
set "strInstallReport="
set "blnNeedsInstall=0"

REM Display header
echo.
echo ========================================
echo  Suno Automation - Windows Setup Script (No Admin)
echo ========================================
echo.
echo This script will set up the Suno Automation project environment.
echo It will skip installation of Git, Node.js, and Python if they're already installed.
echo.

REM Check network connectivity
echo [INFO] Checking network connectivity...
ping -n 1 google.com >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] No internet connection detected. Please check your network and try again.
    echo.
    pause
    exit /b 1
)
echo [SUCCESS] Network connectivity confirmed.
echo.

REM Check if required tools are installed
echo [INFO] Checking for required tools...

REM Check Git
git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Git is not installed. Please install Git manually or run the admin setup script.
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Git is not installed\n"
) else (
    for /f "tokens=*" %%i in ('git --version') do echo [SUCCESS] %%i
)

REM Check Node.js
node --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Node.js is not installed. Please install Node.js manually or run the admin setup script.
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Node.js is not installed\n"
) else (
    for /f "tokens=*" %%i in ('node --version') do echo [SUCCESS] Node.js !strNodeVersion! is installed
)

REM Check Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Python is not installed. Please install Python manually or run the admin setup script.
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Python is not installed\n"
) else (
    for /f "tokens=*" %%i in ('python --version') do echo [SUCCESS] Python !strPythonVersion! is installed
)

if %blnSuccess% neq 1 (
    echo.
    echo [ERROR] Some required tools are missing. Please install them manually or run the admin setup script.
    echo.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] All required tools are installed.
echo.

REM Fetch or refresh repository content
call :setupRepository

REM Setup backend environment
call :setupBackend

REM Setup frontend dependencies
call :setupFrontend

REM Provision environment files
call :setupEnvironmentFiles

REM Display final status
call :displayFinalStatus

goto :eof

REM ========================================
REM Function: setupRepository
REM ========================================
:setupRepository
echo [INFO] Setting up repository...

REM Check if we're in a git repository
if exist ".git" (
    echo [INFO] Repository detected, updating...
    git fetch --all --prune
    if %errorLevel% neq 0 (
        echo [WARNING] Failed to fetch updates, continuing with local version.
    ) else (
        git pull
        if %errorLevel% neq 0 (
            echo [WARNING] Failed to pull updates, continuing with local version.
        ) else (
            echo [SUCCESS] Repository updated successfully.
        )
    )
) else (
    echo [INFO] No git repository found, cloning...
    set "strTargetDir=%USERPROFILE%\%strRepoName%"
    
    REM Create target directory if it doesn't exist
    if not exist "!strTargetDir!" (
        mkdir "!strTargetDir!"
    )
    
    REM Clone the repository
    git clone "%strRepoUrl%" "!strTargetDir!"
    if %errorLevel% neq 0 (
        set "blnSuccess=0"
        set "strInstallReport=!strInstallReport!Failed to clone repository\n"
        echo [ERROR] Failed to clone repository.
        goto :eof
    ) else (
        echo [SUCCESS] Repository cloned to !strTargetDir!
        echo.
        echo [INFO] Changing to cloned repository directory to continue setup...
        cd /d "!strTargetDir!"
        echo [INFO] Now continuing setup in !strTargetDir!
    )
)
goto :eof

REM ========================================
REM Function: setupBackend
REM ========================================
:setupBackend
echo [INFO] Setting up backend environment...

REM Navigate to backend directory
cd backend

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv .venv
    if %errorLevel% neq 0 (
        set "blnSuccess=0"
        set "strInstallReport=!strInstallReport!Failed to create virtual environment\n"
        echo [ERROR] Failed to create virtual environment.
        cd ..
        goto :eof
    )
    echo [SUCCESS] Virtual environment created.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate
if %errorLevel% neq 0 (
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Failed to activate virtual environment\n"
    echo [ERROR] Failed to activate virtual environment.
    cd ..
    goto :eof
)

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip
if %errorLevel% neq 0 (
    echo [WARNING] Failed to upgrade pip, continuing with current version.
)

REM Install requirements
echo [INFO] Installing Python dependencies...
pip install -r requirements.txt
if %errorLevel% neq 0 (
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Failed to install Python dependencies\n"
    echo [ERROR] Failed to install Python dependencies.
    call deactivate
    cd ..
    goto :eof
)
echo [SUCCESS] Python dependencies installed.

REM Fetch Camoufox browser payload
echo [INFO] Downloading Camoufox browser payload...
camoufox fetch
if %errorLevel% neq 0 (
    echo [WARNING] Failed to download Camoufox payload. You may need to run 'camoufox fetch' manually.
) else (
    echo [SUCCESS] Camoufox payload downloaded.
)

REM Deactivate virtual environment
call deactivate

cd ..
echo [SUCCESS] Backend setup completed.
goto :eof

REM ========================================
REM Function: setupFrontend
REM ========================================
:setupFrontend
echo [INFO] Setting up frontend dependencies...

REM Check if frontend directory exists
if not exist "frontend" (
    echo [ERROR] Frontend directory not found.
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Frontend directory not found\n"
    goto :eof
)

REM Navigate to frontend directory
pushd frontend

REM Configure npm to reduce output
npm config set fund false

REM Install dependencies
echo [INFO] Installing Node.js dependencies...
npm install
if %errorLevel% neq 0 (
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Failed to install Node.js dependencies\n"
    echo [ERROR] Failed to install Node.js dependencies.
    popd
    goto :eof
)
echo [SUCCESS] Node.js dependencies installed.

REM Return to original directory
popd
echo [SUCCESS] Frontend setup completed.
goto :eof

REM ========================================
REM Function: setupEnvironmentFiles
REM ========================================
:setupEnvironmentFiles
echo [INFO] Setting up environment files...

REM Create root .env file if it doesn't exist
if not exist ".env" (
    echo [INFO] Creating root .env file...
    (
        echo TAG=latest
        echo CAMOUFOX_SOURCE=auto
    ) > .env
    echo [SUCCESS] Root .env file created.
)

REM Create backend .env file if it doesn't exist
if not exist "backend\.env" (
    echo [INFO] Creating backend .env file...
    if exist "backend\.env.example" (
        copy "backend\.env.example" "backend\.env" >nul 2>&1
        echo [SUCCESS] Backend .env file created from example.
    ) else (
        (
            echo SUPABASE_URL=your-supabase-url
            echo SUPABASE_KEY=your-supabase-key
            echo VITE_SUPABASE_URL=https://your-project.supabase.co
            echo VITE_SUPABASE_KEY=your-vite-supabase-key
            echo USER=your-database-user
            echo PASSWORD=your-database-password
            echo HOST=your-database-host
            echo PORT=5432
            echo DBNAME=postgres
            echo GOOGLE_AI_API_KEY=your-google-ai-api-key
        ) > "backend\.env"
        echo [SUCCESS] Backend .env file created with defaults.
    )
)

REM Create frontend .env file if it doesn't exist
if not exist "frontend\.env" (
    echo [INFO] Creating frontend .env file...
    if exist "frontend\.env.example" (
        copy "frontend\.env.example" "frontend\.env" >nul 2>&1
        echo [SUCCESS] Frontend .env file created from example.
    ) else (
        (
            echo VITE_SUPABASE_URL=your_supabase_url_here
            echo VITE_SUPABASE_KEY=your_supabase_key_here
            echo VITE_API_URL=http://localhost:8000
            echo NODE_ENV=production
        ) > "frontend\.env"
        echo [SUCCESS] Frontend .env file created with defaults.
    )
)

echo [INFO] Environment files have been created with default values.
echo [IMPORTANT] Please edit the .env files to add your actual credentials and API keys.
echo.
goto :eof

REM ========================================
REM Function: displayFinalStatus
REM ========================================
:displayFinalStatus
echo.
echo ========================================
echo  Setup Complete
echo ========================================
echo.

if %blnSuccess% equ 1 (
    echo [SUCCESS] All components have been installed and configured successfully!
    echo.
    echo Your Suno Automation environment is ready to use.
    echo.
    echo Next steps:
    echo 1. Edit the .env files to add your credentials:
    echo    - backend\.env: Add your Supabase and Google AI API keys
    echo    - frontend\.env: Add your Supabase URL and keys
    echo 2. Run 'scripts\windows\start.bat' to launch the application
    echo 3. Run 'scripts\windows\stop.bat' to stop the application
    echo.
    
    REM Ask if user wants to start the application
    set /p strStartApp="Would you like to start the application now? (y/n): "
    if /i "!strStartApp!"=="y" (
        echo [INFO] Starting application...
        if exist "%strScriptRoot%start.bat" (
            call "%strScriptRoot%start.bat"
        ) else (
            echo [WARNING] start.bat not found in scripts/windows directory. Please run it manually when ready.
        )
    )
) else (
    echo [ERROR] Some components failed to install or configure.
    echo.
    echo Installation report:
    echo !strInstallReport!
    echo.
    echo Please resolve the issues above and run the script again.
)

echo.
echo Press any key to exit...
pause >nul
exit /b %blnSuccess%