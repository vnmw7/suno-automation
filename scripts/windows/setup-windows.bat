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
set "INT_NODE_MIN_MAJOR=18"
set "INT_NODE_MIN_MINOR=17"
set "INT_PYTHON_MIN_MAJOR=3"
set "INT_PYTHON_MIN_MINOR=11"

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
if errorlevel 1 (
    echo [ERROR] This script requires administrator privileges for installing software.
    echo Please right-click this script and select "Run as administrator".
    echo.
    pause
    exit /b 1
)

REM Check network connectivity
echo [INFO] Checking network connectivity...
ping -n 1 google.com >nul 2>&1
if errorlevel 1 (
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
if errorlevel 1 (
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
if errorlevel 1 (
    echo [INFO] Installing Git via Winget...
    winget install --exact --accept-package-agreements --accept-source-agreements Git.Git
    if errorlevel 1 (
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
set "strNodeVersion="
set "intNodeMajor="
set "intNodeMinor="
set "blnNodeNeedsUpgrade=0"

node --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing Node.js LTS via Winget...
    winget install --exact --accept-package-agreements --accept-source-agreements OpenJS.NodeJS.LTS
    if errorlevel 1 (
        set "blnSuccess=0"
        set "strInstallReport=!strInstallReport!Failed to install Node.js\n"
        echo [ERROR] Failed to install Node.js.
        goto :eof
    )
    echo [SUCCESS] Node.js installed successfully.
    set "blnNeedsInstall=1"
    call :_refreshNodePath
)

for /f "tokens=2,3 delims=v." %%A in ('node -v 2^>nul') do (
    set "intNodeMajor=%%A"
    set "intNodeMinor=%%B"
)

if defined intNodeMajor (
    set /a intNodeMajor=intNodeMajor+0
    set /a intNodeMinor=intNodeMinor+0
    if !intNodeMajor! LSS %INT_NODE_MIN_MAJOR% (
        set "blnNodeNeedsUpgrade=1"
    ) else if !intNodeMajor! EQU %INT_NODE_MIN_MAJOR% if !intNodeMinor! LSS %INT_NODE_MIN_MINOR% (
        set "blnNodeNeedsUpgrade=1"
    )
) else (
    for /f "tokens=*" %%i in ('node --version 2^>nul') do set "strNodeVersion=%%i"
    if defined strNodeVersion (
        echo [WARNING] Unable to parse Node.js version from !strNodeVersion!. Proceeding with detected installation.
    ) else (
        echo [WARNING] Unable to determine Node.js version. Ensure Node.js >= %INT_NODE_MIN_MAJOR%.%INT_NODE_MIN_MINOR%.
    )
)

if "!blnNodeNeedsUpgrade!"=="1" (
    echo [INFO] Node.js version !intNodeMajor!.!intNodeMinor! does not meet the required %INT_NODE_MIN_MAJOR%.%INT_NODE_MIN_MINOR%. Upgrading to LTS...
    winget upgrade --exact --accept-package-agreements --accept-source-agreements OpenJS.NodeJS.LTS
    if errorlevel 1 (
        echo [WARNING] Node.js upgrade failed. Continuing with existing version.
    ) else (
        echo [SUCCESS] Node.js upgraded to the latest LTS release.
        set "blnNeedsInstall=1"
        call :_refreshNodePath
    )
)

node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not available in this session after installation. Please restart your terminal once the script completes.
    set "strInstallReport=!strInstallReport!Node.js unavailable in current session\n"
    set "blnSuccess=0"
    goto :eof
)

for /f "tokens=*" %%i in ('node --version 2^>nul') do set "strNodeVersion=%%i"
if defined strNodeVersion (
    echo [SUCCESS] Node.js is available (!strNodeVersion!).
) else (
    echo [SUCCESS] Node.js installation verified.
)
goto :eof

REM ========================================
REM Function: ensurePython
REM ========================================
:ensurePython
echo [INFO] Checking Python 3.11 installation...
set "strPythonVersion="
set "intPythonMajor="
set "intPythonMinor="
set "blnPythonNeedsUpgrade=0"

python --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing Python 3.11 via Winget...
    winget install --exact --accept-package-agreements --accept-source-agreements Python.Python.3.11
    if errorlevel 1 (
        set "blnSuccess=0"
        set "strInstallReport=!strInstallReport!Failed to install Python 3.11\n"
        echo [ERROR] Failed to install Python 3.11.
        goto :eof
    )
    echo [SUCCESS] Python 3.11 installed successfully.
    set "blnNeedsInstall=1"
    call :_refreshPythonPath
)

for /f "tokens=2,3 delims= ." %%A in ('python --version 2^>nul') do (
    set "intPythonMajor=%%A"
    set "intPythonMinor=%%B"
)

if defined intPythonMajor (
    set /a intPythonMajor=intPythonMajor+0
    set /a intPythonMinor=intPythonMinor+0
    if !intPythonMajor! LSS %INT_PYTHON_MIN_MAJOR% (
        set "blnPythonNeedsUpgrade=1"
    ) else if !intPythonMajor! EQU %INT_PYTHON_MIN_MAJOR% if !intPythonMinor! LSS %INT_PYTHON_MIN_MINOR% (
        set "blnPythonNeedsUpgrade=1"
    )
) else (
    for /f "tokens=*" %%i in ('python --version 2^>nul') do set "strPythonVersion=%%i"
    if defined strPythonVersion (
        echo [WARNING] Unable to parse Python version from !strPythonVersion!. Proceeding with detected installation.
    ) else (
        echo [WARNING] Unable to determine Python version. Ensure Python >= %INT_PYTHON_MIN_MAJOR%.%INT_PYTHON_MIN_MINOR%.
    )
)

if "!blnPythonNeedsUpgrade!"=="1" (
    echo [INFO] Python version !intPythonMajor!.!intPythonMinor! does not meet the required %INT_PYTHON_MIN_MAJOR%.%INT_PYTHON_MIN_MINOR%. Installing Python.Python.3.11...
    winget upgrade --exact --accept-package-agreements --accept-source-agreements Python.Python.3.11
    if errorlevel 1 (
        echo [WARNING] Python upgrade failed. Continuing with existing version.
    ) else (
        echo [SUCCESS] Python upgraded to 3.11.
        set "blnNeedsInstall=1"
        call :_refreshPythonPath
    )
)

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not available in this session after installation. Please restart your terminal once the script completes.
    set "strInstallReport=!strInstallReport!Python unavailable in current session\n"
    set "blnSuccess=0"
    goto :eof
)

for /f "tokens=*" %%i in ('python --version 2^>nul') do set "strPythonVersion=%%i"
if defined strPythonVersion (
    echo [SUCCESS] Python is available (!strPythonVersion!).
) else (
    echo [SUCCESS] Python installation verified.
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
    if errorlevel 1 (
        echo [WARNING] Failed to fetch updates, continuing with local version.
    ) else (
        git pull
        if errorlevel 1 (
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
if errorlevel 1 (
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
    if errorlevel 1 (
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
if errorlevel 1 (
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Failed to activate virtual environment\n"
    echo [ERROR] Failed to activate virtual environment.
    popd
    goto :eof
)

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [WARNING] Failed to upgrade pip, continuing with current version.
)

echo [INFO] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
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
if errorlevel 1 (
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

where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm not found on PATH. Please restart your terminal or rerun this script after reopening the shell.
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!npm unavailable in current session\n"
    popd
    goto :eof
)

REM Configure npm to reduce output
npm config set fund false

REM Install dependencies
echo [INFO] Installing Node.js dependencies...
npm install
if errorlevel 1 (
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
REM Function: _refreshNodePath
REM ========================================
:_refreshNodePath
set "strNodeExe="
for %%F in (
    "%ProgramFiles%\nodejs\node.exe"
    "%ProgramFiles(x86)%\nodejs\node.exe"
    "%USERPROFILE%\AppData\Local\Programs\nodejs\node.exe"
) do (
    if exist "%%~fF" set "strNodeExe=%%~fF"
)

if defined strNodeExe (
    for %%D in ("!strNodeExe!") do set "strNodeDir=%%~dpD"
    if defined strNodeDir (
        set "PATH=!strNodeDir!;!PATH!"
    )
)
exit /b 0

REM ========================================
REM Function: _refreshPythonPath
REM ========================================
:_refreshPythonPath
set "strPythonExe="
for %%F in (
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python\Python311\python.exe"
) do (
    if exist "%%~fF" set "strPythonExe=%%~fF"
)

if defined strPythonExe (
    for %%D in ("!strPythonExe!") do set "strPythonDir=%%~dpD"
    if defined strPythonDir (
        set "PATH=!strPythonDir!;!PATH!"
    )
)
exit /b 0

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
