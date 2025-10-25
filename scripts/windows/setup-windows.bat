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
set "strProjectRoot=%USERPROFILE%\%strRepoName%"
set "blnRootPushed=0"
set "blnSuccess=1"
set "strInstallReport="
set "blnNeedsInstall=0"
REM NOTE: These are the latest versions as of Oct 2025. Adjust if necessary.
set "INT_NODE_MIN_MAJOR=24"
set "INT_NODE_MIN_MINOR=10"
set "INT_PYTHON_MIN_MAJOR=3"
set "INT_PYTHON_MIN_MINOR=14"

REM Initialize logging
set "strEventSource=Suno Automation Setup"
set "strLogDir=%strScriptRoot%logs"
if not exist "%strLogDir%" mkdir "%strLogDir%"
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set "strDateTime=%%I"
set "strLogFile=%strLogDir%\setup-windows-%strDateTime:~0,8%-%strDateTime:~8,6%.log"

REM Create event source for Windows Event Viewer
eventcreate /ID 1 /L APPLICATION /T INFORMATION /SO "%strEventSource%" /D "Setup script started." >nul 2>&1

REM Log initial message
call :log "INFO" "Suno Automation - Windows Setup Script started."
call :log "INFO" "Log file: %strLogFile%"

REM Display header
echo.
echo ========================================
echo  Suno Automation - Windows Setup Script
echo ========================================
echo.
echo This script will install Git, Node.js, and Python 3.14,
echo then set up the Suno Automation project environment.
echo.

REM Check if running with administrator privileges
net session >> "%strLogFile%" 2>&1
if errorlevel 1 (
    call :log "ERROR" "This script requires administrator privileges for installing software."
    call :log "INFO" "Please right-click this script and select \"Run as administrator\"."
    echo.
    pause
    exit /b 1
)

REM Check network connectivity
call :log "INFO" "Checking network connectivity..."
ping -n 1 google.com >> "%strLogFile%" 2>&1
if errorlevel 1 (
    call :log "ERROR" "No internet connection detected. Please check your network and try again."
    echo.
    pause
    exit /b 1
)
call :log "SUCCESS" "Network connectivity confirmed."
echo.

REM Check if winget is available
call :log "INFO" "Checking for Winget..."
winget --version >> "%strLogFile%" 2>&1
if errorlevel 1 (
    call :log "ERROR" "Winget is not available on this system."
    call :log "INFO" "Please install Windows Package Manager or update your Windows 10/11 installation."
    echo.
    pause
    exit /b 1
)
call :log "SUCCESS" "Winget is available."
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
        call :log "ERROR" "Project root directory \"%strProjectRoot%\" not found."
        set "blnSuccess=0"
        set "strInstallReport=!strInstallReport!Project root directory missing\n"
        set "strProjectRoot="
    )
) else (
    call :log "ERROR" "Unable to determine project root directory."
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
REM Function: log
REM Purpose: Centralized logging to console, file, and Event Viewer
REM ========================================
:log
set "strLogLevel=%~1"
set "strLogMessage=%~2"
set "strEventType=INFORMATION"

REM Format timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set "strLogTime=%%I"
set "strFormattedTime=!strLogTime:~0,4!-!strLogTime:~4,2!-!strLogTime:~6,2! !strLogTime:~8,2!:!strLogTime:~10,2!:!strLogTime:~12,2!"

REM Determine event type based on log level
if /i "%strLogLevel%"=="WARNING" set "strEventType=WARNING"
if /i "%strLogLevel%"=="ERROR" set "strEventType=ERROR"

REM Output to console (all levels)
echo [%strLogLevel%] !strLogMessage!

REM Output to log file (all levels)
echo !strFormattedTime! [%strLogLevel%] !strLogMessage! >> "%strLogFile%"

REM Output to Event Viewer
eventcreate /ID 1 /L APPLICATION /T %strEventType% /SO "%strEventSource%" /D "!strLogMessage!" >nul 2>&1

goto :eof

REM ========================================
REM Function: ensureGit
REM ========================================
:ensureGit
call :log "DEBUG" "Entering :ensureGit"
call :log "INFO" "Checking Git installation..."
git --version >> "%strLogFile%" 2>&1
if errorlevel 1 (
    call :log "INFO" "Installing Git via Winget..."
    winget install --exact --accept-package-agreements --accept-source-agreements Git.Git >> "%strLogFile%" 2>&1
    if errorlevel 1 (
        set "blnSuccess=0"
        set "strInstallReport=!strInstallReport!Failed to install Git\n"
        call :log "ERROR" "Failed to install Git."
    ) else (
        call :log "SUCCESS" "Git installed successfully."
        set "blnNeedsInstall=1"
    )
) else (
    call :log "SUCCESS" "Git is already installed."
)
call :log "DEBUG" "Exiting :ensureGit"
goto :eof

REM ========================================
REM Function: ensureNodeJS
REM ========================================
:ensureNodeJS
call :log "DEBUG" "Entering :ensureNodeJS"
call :log "INFO" "Checking Node.js installation..."
set "strNodeVersion="
set "intNodeMajor="
set "intNodeMinor="
set "blnNodeNeedsUpgrade=0"

node --version >> "%strLogFile%" 2>&1
if errorlevel 1 (
    call :log "INFO" "Installing Node.js LTS via Winget..."
    winget install --exact --accept-package-agreements --accept-source-agreements OpenJS.NodeJS.LTS >> "%strLogFile%" 2>&1
    if errorlevel 1 (
        set "blnSuccess=0"
        set "strInstallReport=!strInstallReport!Failed to install Node.js\n"
        call :log "ERROR" "Failed to install Node.js."
        call :log "DEBUG" "Exiting :ensureNodeJS"
        goto :eof
    )
    call :log "SUCCESS" "Node.js installed successfully."
    set "blnNeedsInstall=1"
    call :_refreshNodePath
)

for /f "tokens=2,3 delims=v." %%A in ('node -v 2^>^&1') do (
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
    for /f "tokens=*" %%i in ('node --version 2^>^&1') do set "strNodeVersion=%%i"
    if defined strNodeVersion (
        call :log "WARNING" "Unable to parse Node.js version from !strNodeVersion!. Proceeding with detected installation."
    ) else (
        call :log "WARNING" "Unable to determine Node.js version. Ensure Node.js >= %INT_NODE_MIN_MAJOR%.%INT_NODE_MIN_MINOR%."
    )
)

if "!blnNodeNeedsUpgrade!"=="1" (
    call :log "INFO" "Node.js version !intNodeMajor!.!intNodeMinor! does not meet the required %INT_NODE_MIN_MAJOR%.%INT_NODE_MIN_MINOR%. Upgrading to LTS..."
    winget upgrade --exact --accept-package-agreements --accept-source-agreements OpenJS.NodeJS.LTS >> "%strLogFile%" 2>&1
    if errorlevel 1 (
        call :log "WARNING" "Node.js upgrade failed. Continuing with existing version."
    ) else (
        call :log "SUCCESS" "Node.js upgraded to the latest LTS release."
        set "blnNeedsInstall=1"
        call :_refreshNodePath
    )
)

node --version >> "%strLogFile%" 2>&1
if errorlevel 1 (
    call :log "ERROR" "Node.js is not available in this session after installation. Please restart your terminal once the script completes."
    set "strInstallReport=!strInstallReport!Node.js unavailable in current session\n"
    set "blnSuccess=0"
    call :log "DEBUG" "Exiting :ensureNodeJS"
    goto :eof
)

for /f "tokens=*" %%i in ('node --version 2^>^&1') do set "strNodeVersion=%%i"
if defined strNodeVersion (
    call :log "SUCCESS" "Node.js is available (!strNodeVersion!)."
) else (
    call :log "SUCCESS" "Node.js installation verified."
)
call :log "DEBUG" "Exiting :ensureNodeJS"
goto :eof

REM ========================================
REM Function: ensurePython
REM ========================================
:ensurePython
call :log "DEBUG" "Entering :ensurePython"
call :log "INFO" "Checking Python 3.14 installation..."
set "strPythonVersion="
set "intPythonMajor="
set "intPythonMinor="
set "blnPythonNeedsUpgrade=0"

python --version >> "%strLogFile%" 2>&1
if errorlevel 1 (
    call :log "INFO" "Installing Python 3.11 via Winget..."
    winget install --exact --accept-package-agreements --accept-source-agreements Python.Python.3.14 >> "%strLogFile%" 2>&1
    if errorlevel 1 (
        set "blnSuccess=0"
        set "strInstallReport=!strInstallReport!Failed to install Python 3.14\n"
        call :log "ERROR" "Failed to install Python 3.14."
        call :log "DEBUG" "Exiting :ensurePython"
        goto :eof
    )
    call :log "SUCCESS" "Python 3.14 installed successfully."
    set "blnNeedsInstall=1"
    call :_refreshPythonPath
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do (
    set "strPythonVersionRaw=%%v"
)
for /f "tokens=2,3 delims=." %%A in ("!strPythonVersionRaw:python =!") do (
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
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set "strPythonVersion=%%i"
    if defined strPythonVersion (
        call :log "WARNING" "Unable to parse Python version from !strPythonVersion!. Proceeding with detected installation."
    ) else (
        call :log "WARNING" "Unable to determine Python version. Ensure Python >= %INT_PYTHON_MIN_MAJOR%.%INT_PYTHON_MIN_MINOR%."
    )
)

if "!blnPythonNeedsUpgrade!"=="1" (
    call :log "INFO" "Python version !intPythonMajor!.!intPythonMinor! does not meet the required %INT_PYTHON_MIN_MAJOR%.%INT_PYTHON_MIN_MINOR%. Installing Python.Python.3.14..."
    winget upgrade --exact --accept-package-agreements --accept-source-agreements Python.Python.3.14 >> "%strLogFile%" 2>&1
    if errorlevel 1 (
        call :log "WARNING" "Python upgrade failed. Continuing with existing version."
    ) else (
        call :log "SUCCESS" "Python upgraded to 3.14."
        set "blnNeedsInstall=1"
        call :_refreshPythonPath
    )
)

python --version >> "%strLogFile%" 2>&1
if errorlevel 1 (
    call :log "ERROR" "Python is not available in this session after installation. Please restart your terminal once the script completes."
    set "strInstallReport=!strInstallReport!Python unavailable in current session\n"
    set "blnSuccess=0"
    call :log "DEBUG" "Exiting :ensurePython"
    goto :eof
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set "strPythonVersion=%%i"
if defined strPythonVersion (
    call :log "SUCCESS" "Python is available (!strPythonVersion!)."
) else (
    call :log "SUCCESS" "Python installation verified."
)
call :log "DEBUG" "Exiting :ensurePython"
goto :eof

REM ========================================
REM Function: setupRepository
REM ========================================
:setupRepository
call :log "DEBUG" "Entering :setupRepository"
call :log "INFO" "Setting up repository at !strProjectRoot!..."

REM Check if the repository directory already exists
if exist "!strProjectRoot!\.git" (
    call :log "INFO" "Existing repository found. Updating..."
    pushd "!strProjectRoot!"
    git pull >> "%strLogFile%" 2>&1
    if errorlevel 1 (
        call :log "WARNING" "Failed to pull updates. Continuing with the local version."
    ) else (
        call :log "SUCCESS" "Repository updated successfully."
    )
    popd
) else (
    call :log "INFO" "No existing repository found. Cloning a fresh copy..."
    REM Create the target directory if it doesn't exist
    if not exist "!strProjectRoot!" (
        mkdir "!strProjectRoot!"
    )
    
    REM Clone the repository
    git clone "%strRepoUrl%" "!strProjectRoot!" >> "%strLogFile%" 2>&1
    if errorlevel 1 (
        set "blnSuccess=0"
        set "strInstallReport=!strInstallReport!Failed to clone repository\n"
        call :log "ERROR" "Failed to clone repository."
        call :log "DEBUG" "Exiting :setupRepository"
        goto :eof
    )
    call :log "SUCCESS" "Repository cloned to !strProjectRoot!"
)
call :log "DEBUG" "Exiting :setupRepository"
goto :eof

REM ========================================
REM Function: setupBackend
REM ========================================
:setupBackend
call :log "DEBUG" "Entering :setupBackend"
call :log "INFO" "Setting up backend environment..."

if not defined strProjectRoot (
    call :log "ERROR" "Project root is not defined. Unable to configure backend."
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Project root missing for backend setup\n"
    call :log "DEBUG" "Exiting :setupBackend"
    goto :eof
)

if not exist "%strProjectRoot%\backend" (
    call :log "ERROR" "Backend directory not found at \"%strProjectRoot%\backend\"."
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Backend directory not found\n"
    call :log "DEBUG" "Exiting :setupBackend"
    goto :eof
)

pushd "%strProjectRoot%\backend"

if not exist ".venv" (
    call :log "INFO" "Creating Python virtual environment..."
    python -m venv .venv >> "%strLogFile%" 2>&1
    if errorlevel 1 (
        set "blnSuccess=0"
        set "strInstallReport=!strInstallReport!Failed to create virtual environment\n"
        call :log "ERROR" "Failed to create virtual environment."
        popd
        call :log "DEBUG" "Exiting :setupBackend"
        goto :eof
    )
    call :log "SUCCESS" "Virtual environment created."
)

call :log "INFO" "Activating virtual environment..."
call .venv\Scripts\activate >> "%strLogFile%" 2>&1
if errorlevel 1 (
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Failed to activate virtual environment\n"
    call :log "ERROR" "Failed to activate virtual environment."
    popd
    call :log "DEBUG" "Exiting :setupBackend"
    goto :eof
)

call :log "INFO" "Upgrading pip..."
python -m pip install --upgrade pip >> "%strLogFile%" 2>&1
if errorlevel 1 (
    call :log "WARNING" "Failed to upgrade pip, continuing with current version."
)

call :log "INFO" "Installing Python dependencies..."
pip install -r requirements.txt >> "%strLogFile%" 2>&1
if errorlevel 1 (
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Failed to install Python dependencies\n"
    call :log "ERROR" "Failed to install Python dependencies."
    call deactivate
    popd
    call :log "DEBUG" "Exiting :setupBackend"
    goto :eof
)
call :log "SUCCESS" "Python dependencies installed."

call :log "INFO" "Downloading Camoufox browser payload..."
camoufox fetch >> "%strLogFile%" 2>&1
if errorlevel 1 (
    call :log "WARNING" "Failed to download Camoufox payload. You may need to run 'camoufox fetch' manually."
) else (
    call :log "SUCCESS" "Camoufox payload downloaded."
)

call deactivate
popd
call :log "SUCCESS" "Backend setup completed."
call :log "DEBUG" "Exiting :setupBackend"
goto :eof

REM ========================================
REM Function: setupFrontend
REM ========================================
:setupFrontend
call :log "DEBUG" "Entering :setupFrontend"
call :log "INFO" "Setting up frontend dependencies..."

REM Check if frontend directory exists
if not defined strProjectRoot (
    call :log "ERROR" "Project root is not defined. Unable to configure frontend."
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Project root missing for frontend setup\n"
    call :log "DEBUG" "Exiting :setupFrontend"
    goto :eof
)

if not exist "%strProjectRoot%\frontend" (
    call :log "ERROR" "Frontend directory not found at \"%strProjectRoot%\frontend\"."
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Frontend directory not found\n"
    call :log "DEBUG" "Exiting :setupFrontend"
    goto :eof
)

REM Navigate to frontend directory
pushd "%strProjectRoot%\frontend"

where npm >> "%strLogFile%" 2>&1
if errorlevel 1 (
    call :log "ERROR" "npm not found on PATH. Please restart your terminal or rerun this script after reopening the shell."
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!npm unavailable in current session\n"
    popd
    call :log "DEBUG" "Exiting :setupFrontend"
    goto :eof
)

REM Configure npm to reduce output
npm config set fund false >> "%strLogFile%" 2>&1

REM Install dependencies
call :log "INFO" "Installing Node.js dependencies..."
npm install >> "%strLogFile%" 2>&1
if errorlevel 1 (
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Failed to install Node.js dependencies\n"
    call :log "ERROR" "Failed to install Node.js dependencies."
    popd
    call :log "DEBUG" "Exiting :setupFrontend"
    goto :eof
)
call :log "SUCCESS" "Node.js dependencies installed."

REM Return to original directory
popd
call :log "SUCCESS" "Frontend setup completed."
call :log "DEBUG" "Exiting :setupFrontend"
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
    "%LocalAppData%\Programs\Python\Python314\python.exe"
    "%ProgramFiles%\Python314\python.exe"
    "%ProgramFiles%\Python\Python314\python.exe"
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
call :log "DEBUG" "Entering :setupEnvironmentFiles"
call :log "INFO" "Setting up environment files..."

if not defined strProjectRoot (
    call :log "ERROR" "Project root is not defined. Unable to create environment files."
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Project root missing for environment files\n"
    call :log "DEBUG" "Exiting :setupEnvironmentFiles"
    goto :eof
)

if not exist "%strProjectRoot%" (
    call :log "ERROR" "Project root directory \"%strProjectRoot%\" not found. Unable to create environment files."
    set "blnSuccess=0"
    set "strInstallReport=!strInstallReport!Project root directory not found for environment files\n"
    call :log "DEBUG" "Exiting :setupEnvironmentFiles"
    goto :eof
)

REM Create root .env file if it doesn't exist
if not exist "%strProjectRoot%\.env" (
    call :log "INFO" "Creating root .env file..."
    (
        echo TAG=latest
        echo CAMOUFOX_SOURCE=auto
    ) > "%strProjectRoot%\.env"
    call :log "SUCCESS" "Root .env file created."
)

REM Create backend .env file if it doesn't exist
if not exist "%strProjectRoot%\backend\.env" (
    call :log "INFO" "Creating backend .env file..."
    if exist "%strProjectRoot%\backend\.env.example" (
        copy "%strProjectRoot%\backend\.env.example" "%strProjectRoot%\backend\.env" >> "%strLogFile%" 2>&1
        call :log "SUCCESS" "Backend .env file created from example."
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
        call :log "SUCCESS" "Backend .env file created with defaults."
    )
)

REM Create frontend .env file if it doesn't exist
if not exist "%strProjectRoot%\frontend\.env" (
    call :log "INFO" "Creating frontend .env file..."
    if exist "%strProjectRoot%\frontend\.env.example" (
        copy "%strProjectRoot%\frontend\.env.example" "%strProjectRoot%\frontend\.env" >> "%strLogFile%" 2>&1
        call :log "SUCCESS" "Frontend .env file created from example."
    ) else (
        (
            echo VITE_SUPABASE_URL=your_supabase_url_here
            echo VITE_SUPABASE_KEY=your_supabase_key_here
            echo VITE_API_URL=http://localhost:8000
            echo NODE_ENV=production
        ) > "%strProjectRoot%\frontend\.env"
        call :log "SUCCESS" "Frontend .env file created with defaults."
    )
)

call :log "INFO" "Environment files have been created with default values."
call :log "IMPORTANT" "Please edit the .env files to add your actual credentials and API keys."
call :log "DEBUG" "Exiting :setupEnvironmentFiles"
goto :eof

REM ========================================
REM Function: displayFinalStatus
REM ========================================
:displayFinalStatus
call :log "DEBUG" "Entering :displayFinalStatus"
echo.
echo ========================================
echo  Setup Complete
echo ========================================
echo.

if %blnSuccess% equ 1 (
    call :log "SUCCESS" "All components have been installed and configured successfully!"
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
        call :log "INFO" "Starting application..."
        if exist "!strStartScript!" (
            call "!strStartScript!"
        ) else (
            call :log "WARNING" "start.bat not found at \"!strStartScript!\". Please run it manually when ready."
        )
    )
) else (
    call :log "ERROR" "Setup failed. See details below."
    echo.
    echo ========================================
    echo  Setup Failed
    echo ========================================
    echo.
    echo The following issues were reported:
    if defined strInstallReport (
        echo !strInstallReport!
    ) else (
        echo - An unexpected error occurred.
    )
    echo.
    echo Please check the log file for a complete execution trace:
    echo %strLogFile%
)

call :log "INFO" "Setup script completed. Log file saved to: %strLogFile%"
echo.
echo Log file saved to: %strLogFile%
echo You can also check the Windows Event Viewer for 'Suno Automation Setup' events.
echo.
echo Press any key to exit...
pause >nul
call :log "DEBUG" "Exiting :displayFinalStatus"
exit /b %blnSuccess%
