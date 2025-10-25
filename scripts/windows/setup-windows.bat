@echo off
REM System: Suno Automation
REM Module: Windows Setup Automation
REM File URL: setup-windows.bat
REM Purpose: One-click Windows bootstrap script that provisions all project prerequisites

SetLocal EnableExtensions EnableDelayedExpansion

REM Initialize variables
set "strRepoUrl=https://github.com/vnmw7/suno-automation.git"
set "strRepoName=suno-automation"
set "strScriptRoot=%~dp0"
set "strProjectRoot="
set "blnRootPushed=0"
set "blnSuccess=1"
set "strInstallReport="
set "blnNeedsInstall=0"

for %%I in ("%~dp0..\..") do set "strDefaultRepo=%%~fI"
if exist "%strDefaultRepo%\.git" (
    set "strProjectRoot=%strDefaultRepo%"
)
set "strDefaultRepo="

REM Display header
echo.
echo ========================================
echo  Suno Automation - Windows Setup Script
echo ========================================
echo.
echo This script will install Git, Node.js, and Python 3.11,
echo then set up the Suno Automation project environment.
echo.

REM Check if running with administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script requires administrator privileges for installing software.
    echo Please right-click this script and select "Run as administrator".
    echo.
    pause
    exit /b 1
)

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

REM Check if winget is available
echo [INFO] Checking for Winget...
winget --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Winget is not available on this system.
    echo Please install Windows Package Manager or update your Windows 10/11 installation.
    echo.
    pause
    exit /b 1
)
echo [SUCCESS] Winget is available.
echo.

REM Ensure core toolchain
call :ensureGit
call :ensureNodeJS
call :ensurePython

REM Fetch or refresh repository content
call :setupRepository

REM Prepare project root context
if defined strProjectRoot (
    if exist "%strProjectRoot%" (
        pushd "%strProjectRoot%"
        set "blnRootPushed=1"
    ) else (
        echo [ERROR] Project root directory "%strProjectRoot%" not found.
        set "blnSuccess=0"
        set "strInstallReport=!strInstallReport!Project root directory missing\n"
        set "strProjectRoot="
    )
) else (
    echo [ERROR] Unable to determine project root directory.
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Project root not resolved\n"
)

if defined strProjectRoot (
    REM Setup backend environment
    call :setupBackend

    REM Setup frontend dependencies
    call :setupFrontend

    REM Provision environment files
    call :setupEnvironmentFiles
) else (
    echo [WARNING] Skipping backend, frontend, and environment setup because the project root is unavailable.
)

if "!blnRootPushed!"=="1" (
    popd
    set "blnRootPushed=0"
)

REM Display final status
call :displayFinalStatus

goto :eof

REM ========================================
REM Function: ensureGit
REM ========================================
:ensureGit
echo [INFO] Checking Git installation...
git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Installing Git via Winget...
    winget install --exact --accept-package-agreements --accept-source-agreements Git.Git
    if %errorLevel% neq 0 (
        set "blnSuccess=0"
        set "strInstallReport=!strInstallReport!Failed to install Git\n"
        echo [ERROR] Failed to install Git.
    ) else (
        echo [SUCCESS] Git installed successfully.
        set "blnNeedsInstall=1"
    )
) else (
    echo [SUCCESS] Git is already installed.
)
goto :eof

REM ========================================
REM Function: ensureNodeJS
REM ========================================
:ensureNodeJS
echo [INFO] Checking Node.js installation...
node --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Installing Node.js LTS via Winget...
    winget install --exact --accept-package-agreements --accept-source-agreements OpenJS.NodeJS.LTS
    if %errorLevel% neq 0 (
        set "blnSuccess=0"
        set "strInstallReport=!strInstallReport!Failed to install Node.js\n"
        echo [ERROR] Failed to install Node.js.
    ) else (
        echo [SUCCESS] Node.js installed successfully.
        set "blnNeedsInstall=1"
    )
) else (
    for /f "tokens=*" %%i in ('node --version') do set strNodeVersion=%%i
    echo [SUCCESS] Node.js is already installed (!strNodeVersion!).
)
goto :eof

REM ========================================
REM Function: ensurePython
REM ========================================
:ensurePython
echo [INFO] Checking Python 3.11 installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Installing Python 3.11 via Winget...
    winget install --exact --accept-package-agreements --accept-source-agreements Python.Python.3.11
    if %errorLevel% neq 0 (
        set "blnSuccess=0"
        set "strInstallReport=!strInstallReport!Failed to install Python 3.11\n"
        echo [ERROR] Failed to install Python 3.11.
    ) else (
        echo [SUCCESS] Python 3.11 installed successfully.
        set "blnNeedsInstall=1"
    )
) else (
    for /f "tokens=*" %%i in ('python --version') do set strPythonVersion=%%i
    echo [SUCCESS] Python is already installed (!strPythonVersion!).
)
goto :eof

REM ========================================
REM Function: setupRepository
REM ========================================
:setupRepository
echo [INFO] Setting up repository...

if defined strProjectRoot (
    echo [INFO] Repository detected at !strProjectRoot!, updating...
    pushd "!strProjectRoot!"
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
    popd
    goto :eof
)

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
)

echo [SUCCESS] Repository cloned to !strTargetDir!
set "strProjectRoot=!strTargetDir!"
echo [INFO] Project root set to !strProjectRoot!
goto :eof

REM ========================================
REM Function: setupBackend
REM ========================================
:setupBackend
echo [INFO] Setting up backend environment...

if not defined strProjectRoot (
    echo [ERROR] Project root is not defined. Unable to configure backend.
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Project root missing for backend setup\n"
    goto :eof
)

if not exist "%strProjectRoot%\backend" (
    echo [ERROR] Backend directory not found at "%strProjectRoot%\backend".
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Backend directory not found\n"
    goto :eof
)

pushd "%strProjectRoot%\backend"

if not exist ".venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv .venv
    if %errorLevel% neq 0 (
        set "blnSuccess=0"
        set "strInstallReport=!strInstallReport!Failed to create virtual environment\n"
        echo [ERROR] Failed to create virtual environment.
        popd
        goto :eof
    )
    echo [SUCCESS] Virtual environment created.
)

echo [INFO] Activating virtual environment...
call .venv\Scripts\activate
if %errorLevel% neq 0 (
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Failed to activate virtual environment\n"
    echo [ERROR] Failed to activate virtual environment.
    popd
    goto :eof
)

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip
if %errorLevel% neq 0 (
    echo [WARNING] Failed to upgrade pip, continuing with current version.
)

echo [INFO] Installing Python dependencies...
pip install -r requirements.txt
if %errorLevel% neq 0 (
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Failed to install Python dependencies\n"
    echo [ERROR] Failed to install Python dependencies.
    call deactivate
    popd
    goto :eof
)
echo [SUCCESS] Python dependencies installed.

echo [INFO] Downloading Camoufox browser payload...
camoufox fetch
if %errorLevel% neq 0 (
    echo [WARNING] Failed to download Camoufox payload. You may need to run 'camoufox fetch' manually.
) else (
    echo [SUCCESS] Camoufox payload downloaded.
)

call deactivate
popd
echo [SUCCESS] Backend setup completed.
goto :eof

REM ========================================
REM Function: setupFrontend
REM ========================================
:setupFrontend
echo [INFO] Setting up frontend dependencies...

REM Check if frontend directory exists
if not defined strProjectRoot (
    echo [ERROR] Project root is not defined. Unable to configure frontend.
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Project root missing for frontend setup\n"
    goto :eof
)

if not exist "%strProjectRoot%\frontend" (
    echo [ERROR] Frontend directory not found at "%strProjectRoot%\frontend".
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Frontend directory not found\n"
    goto :eof
)

REM Navigate to frontend directory
pushd "%strProjectRoot%\frontend"

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

if not defined strProjectRoot (
    echo [ERROR] Project root is not defined. Unable to create environment files.
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Project root missing for environment files\n"
    goto :eof
)

if not exist "%strProjectRoot%" (
    echo [ERROR] Project root directory "%strProjectRoot%" not found. Unable to create environment files.
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Project root directory not found for environment files\n"
    goto :eof
)

REM Create root .env file if it doesn't exist
if not exist "%strProjectRoot%\.env" (
    echo [INFO] Creating root .env file...
    (
        echo TAG=latest
        echo CAMOUFOX_SOURCE=auto
    ) > "%strProjectRoot%\.env"
    echo [SUCCESS] Root .env file created.
)

REM Create backend .env file if it doesn't exist
if not exist "%strProjectRoot%\backend\.env" (
    echo [INFO] Creating backend .env file...
    if exist "%strProjectRoot%\backend\.env.example" (
        copy "%strProjectRoot%\backend\.env.example" "%strProjectRoot%\backend\.env" >nul 2>&1
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
        ) > "%strProjectRoot%\backend\.env"
        echo [SUCCESS] Backend .env file created with defaults.
    )
)

REM Create frontend .env file if it doesn't exist
if not exist "%strProjectRoot%\frontend\.env" (
    echo [INFO] Creating frontend .env file...
    if exist "%strProjectRoot%\frontend\.env.example" (
        copy "%strProjectRoot%\frontend\.env.example" "%strProjectRoot%\frontend\.env" >nul 2>&1
        echo [SUCCESS] Frontend .env file created from example.
    ) else (
        (
            echo VITE_SUPABASE_URL=your_supabase_url_here
            echo VITE_SUPABASE_KEY=your_supabase_key_here
            echo VITE_API_URL=http://localhost:8000
            echo NODE_ENV=production
        ) > "%strProjectRoot%\frontend\.env"
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
    if defined strProjectRoot (
        set "strStartScript=%strProjectRoot%\scripts\windows\start.bat"
    ) else (
        set "strStartScript=%strScriptRoot%start.bat"
    )
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
        if exist "!strStartScript!" (
            call "!strStartScript!"
        ) else (
            echo [WARNING] start.bat not found at "!strStartScript!". Please run it manually when ready.
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
