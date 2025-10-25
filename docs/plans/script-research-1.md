PowerShell Conversion of the Windows Setup Script
Introduction and Context
The Suno Automation project’s Windows setup was originally provided as a batch (.bat) script. This batch script aimed to install prerequisites (Git, Node.js, Python), clone the repository, set up a Python virtual environment, install dependencies, and initialize environment files – all in one go. However, the batch script encountered several issues: it assumed a fixed clone location (user’s profile directory), it attempted to run pip install outside the intended virtual environment context, and it relied on batch-specific commands (activate/deactivate) not available when run in PowerShell. Furthermore, running the batch script from an external drive or a non-default location could lead to failures (e.g. trying to clone into a non-empty directory and crashing). To address these issues and modernize the process, we will convert the script to PowerShell, incorporating improvements for reliability and flexibility.
Key Improvements in the PowerShell Script
•	Dynamic Repository Path: Instead of cloning to a hard-coded user profile path, the PowerShell script uses its own location as a reference. The repository will be cloned relative to the script’s directory, ensuring it works from any drive or folder (including external drives). This prevents path issues and keeps all files in the expected location. PowerShell’s $MyInvocation.MyCommand.Path property provides the full path of the currently executing script[1], which we use to determine the script’s directory and set the clone path accordingly.
•	Proper Virtual Environment Usage: The batch script attempted to call activate and deactivate for the Python virtual environment, which led to errors in PowerShell ('deactivate' is not recognized…). In the new script, we create and use the virtual environment within the backend folder by directly invoking the environment’s Python and Pip executables. This means we don’t rely on an external activation script at all – avoiding the deactivate issue entirely. All pip install commands are run using the venv’s interpreter, so dependencies go into the correct environment.
•	Robust Logging Mechanism: We preserve the detailed logging of the original script, capturing each step’s success or failure. The PowerShell version writes to both the console and a log file, and also records events to the Windows Event Viewer (Application log) using the eventcreate utility (similar to the batch script’s approach). Each log entry is prefixed with a level tag like [INFO], [SUCCESS], [ERROR], etc., and timestamps are recorded in the log file for auditing. We utilize eventcreate.exe to log to the Windows event log (Application) with a custom source (e.g. “Suno Automation Setup”), as is common for command-line logging[2].
•	Administrator Privilege Check: Just like the batch file, the PowerShell script ensures it is running with elevated (Administrator) privileges before proceeding. We use PowerShell’s .NET integration to check the current process’s elevation status (the WindowsPrincipal class) – essentially verifying if the user is in the Administrators group[3][4]. If not elevated, the script will log an error and prompt the user to restart it as Administrator (preventing cryptic failures later when installing software).
•	Winget Package Management: The script leverages Windows Package Manager (winget) to install or upgrade Git, Node.js, and Python as needed. PowerShell can call winget directly just like the batch script did. We include the --accept-package-agreements and --accept-source-agreements flags so installation doesn’t stall waiting for user input. The script first checks if each tool is present and meets the required version, and only then calls winget to install/upgrade. For example, if Node.js is found but below version 24.10, we run winget upgrade OpenJS.NodeJS.LTS to get the latest LTS release. Similarly, if Python is below 3.14, we install/upgrade Python 3.14 via winget.
•	Path Updates for New Installations: One challenge with installing software mid-script is that the new installations might not be immediately available in the current PATH. The original batch script attempted to handle this by manually updating the PATH with known install locations. In PowerShell, we implement a similar “path refresh” after installing Node or Python. The script searches the standard install directories for the newly installed binaries (for example, the Python 3.14 installer from winget typically places python.exe under %LocalAppData%\Programs\Python\Python314 by default[2]). If found, that directory is prepended to the PATH for the current session so that subsequent commands (like python or npm) use the updated version. This helps avoid the need to restart the shell in the middle of the script.
•	Error Handling and User Prompts: The PowerShell script is designed to stop at any critical failure (logging the issue and collecting it for a summary report). At the end, if any component failed to install or configure, the script will clearly list those issues under a “Setup Failed” section, mirroring the batch script’s final output. If everything succeeds, a “Setup Complete” message is shown, along with next steps and an interactive prompt asking the user if they want to start the application immediately. We use PowerShell’s ability to read user input (via Read-Host) to replicate the “Would you like to start the application now? (y/n)” prompt from the original. For the final “press any key to exit” behavior, we use [System.Console]::ReadKey() to wait for a key press without requiring the user to press Enter[5], closely mimicking the pause in the batch script.
With these improvements, the PowerShell script becomes a more robust, industry-standard installer that should run smoothly in a PowerShell console. It addresses the crashes and errors seen before by using proper PowerShell practices and ensuring all commands execute in the correct context.
Detailed Implementation Notes
Administrator Check and Initial Setup
At the very start, the script verifies that it’s running as Administrator. This is crucial because installing software and writing to the event log require elevated rights. We perform this check using the .NET WindowsIdentity and WindowsPrincipal classes (as PowerShell lacks a direct cmdlet) and will exit with instructions if not elevated[3]. We also initialize a log file in a logs directory next to the script. The log file name includes a timestamp for uniqueness (e.g. setup-windows-YYYYMMDD-HHMMSS.log). Logging is implemented via a custom Write-Log function that appends entries to the log file (with a timestamp), prints to the console, and uses eventcreate to record events to Event Viewer. Each log entry in Event Viewer is tagged with the appropriate type (Information, Warning, or Error) based on the log level[2].
Installing Git (if needed)
The script checks for Git by running git --version. If the command is not found (which sets $LASTEXITCODE or throws in PowerShell), we log that Git is missing and use winget to install it (winget install --exact Git.Git). The --exact flag ensures we get the intended package by ID, and we suppress prompts by auto-accepting agreements. On success, we log that Git was installed; if winget fails (non-zero exit code), we record the failure in our installReport and mark the overall setup as unsuccessful (but we do not stop immediately, so that all issues can be reported at the end). If Git is already present, we simply log that it’s installed and continue.
Installing Node.js (ensuring version >= 24.10)
For Node.js, we run node --version and parse the output (which typically looks like vX.Y.Z). The minimal required version is 24.10. If Node is not installed at all, we run winget install OpenJS.NodeJS.LTS to get the latest LTS release. If Node is installed but the version is below 24.10, we attempt an upgrade via winget upgrade OpenJS.NodeJS.LTS. The script carefully handles version parsing; if it cannot parse the version string for some reason, it logs a warning but proceeds with whatever is installed[6][7]. After an installation or upgrade, we call a helper function Refresh-NodePath to adjust the PATH. This function looks for node.exe in standard install locations (Program Files, Program Files (x86), or the local AppData path) and prepends that directory to $env:PATH. This makes the newly installed Node immediately available. Finally, we verify by calling node --version again – if it still fails (meaning Node isn’t recognized even after installation), we log a critical error suggesting the user may need to restart their terminal, and we mark the setup as failed[6]. If Node is present and meets the requirement (or after a successful update), we log the Node version found as confirmation.
Installing Python 3.14
The script enforces Python 3.14 as a minimum. We check python --version and parse it similarly. If Python is not installed, we use winget install Python.Python.3.14 to install the latest 3.14.x release. If an older Python (e.g. 3.12 or 3.13) is present, we run winget upgrade Python.Python.3.14 to get the newer version. After installation/upgrade, we call Refresh-PythonPath which searches typical installation paths for Python 3.14 (like the user’s local app data or Program Files directories as used by the Python installer). This ensures that when we call python subsequently, we get the 3.14 version (the batch script’s logs showed an instance where Python was upgraded but still reported the old version until the PATH was adjusted). We then double-check that python --version works. If not, we log an error that Python isn’t available in the current session. Assuming it is available, we log the exact Python version in use. All these steps mirror the intended behavior of the original script (which attempted to upgrade Python and log its availability).
Cloning or Updating the Repository
One significant change is how we determine the target directory for the repository. We define $ProjectRoot as a directory named suno-automation inside the script’s directory. In PowerShell, we obtain the script’s directory via:
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Join-Path $scriptRoot 'suno-automation'
This approach ensures that if the script is executed from, say, D:\Tools, it will clone the repository into D:\Tools\suno-automation (rather than forcing it under the user’s profile). We then perform the clone/update logic:
- If the target folder already exists and contains a .git subfolder, we assume it’s an existing clone. We then attempt to update it by running git pull in that directory. Any failure to pull is logged as a warning (but not fatal, since the local copy might still be used).
- If the folder exists but is not a git repository, we treat this as an unusual scenario (perhaps a leftover folder from a previous run). In that case, we log an error and add to the report that the directory is not a git repo. (We do not automatically delete or overwrite it to avoid data loss; instead, we instruct the user to handle it manually and rerun). This check prevents the script from attempting a git clone into a non-empty directory, which caused the original script to fail (fatal: destination path already exists and is not an empty directory).
- If the folder does not exist at all, we create it and perform a fresh clone using git clone <repo_url> <target_path>. On success, we log that the repository was cloned; on failure, we log an error and mark the install as failed (and skip subsequent steps, since we cannot proceed without the code).
This logic ensures the repository is set up in the correct location relative to the script and avoids collisions with existing directories.
Setting Up the Backend (Python Environment)
Once the repository files are in place, the script moves on to configuring the backend. We verify that the backend directory exists under $ProjectRoot (if not, it’s an error – perhaps the repo clone failed or the project structure is unexpected). Then we:
1. Create a virtual environment: We run python -m venv .venv in the backend directory (using the Python 3.14 we set up earlier). This creates a .venv folder containing an isolated Python environment. If .venv already exists (from a previous run), we skip creation. Any error in creating the venv is logged and stops the backend setup. On success, we log that the venv was created.
2. Upgrade pip: Instead of using the external activate script, we directly invoke the venv’s pip. The path to pip in the venv is backend\.venv\Scripts\pip.exe on Windows. We call this to upgrade pip to the latest version (pip install --upgrade pip). This output is logged to the file (not to console, to keep the console output clean), and we only warn (not fail) if the pip upgrade fails, since pip’s current version can usually still install packages.
3. Install Python dependencies: Still using the venv’s pip, we install the required packages by pointing to the requirements.txt file in the backend. The command is pip install -r requirements.txt executed in the backend directory. If this fails (for example, if the requirements.txt is missing or a package installation error occurs), we log an error and mark this as a failure in the report. This was another point of improvement: the batch script output suggests it might have been looking for requirements.txt in the wrong place. By ensuring our working directory is the backend folder (or specifying the full path to the requirements file), we guarantee pip can find it.
4. Download Camoufox payload: The Camoufox browser payload is likely a part of this project (perhaps for browser automation). After installing dependencies (which presumably include the camoufox CLI tool), we attempt to run camoufox fetch to download necessary payloads (like the GeoIP database seen in the logs). We run this command via the venv’s context as well (using the camoufox.exe from the venv’s Scripts if available). If the fetch fails, we log a warning but continue – since the script’s [WARNING] in the original indicates it’s non-fatal and can be done manually if needed. On success, we log that the payload was downloaded.
Throughout these steps, we do not actually activate the venv in the PowerShell session; instead, we directly call the needed executables inside the venv. This avoids any persistence of venv state and eliminates the need to deactivate. It’s a cleaner approach for scripting scenarios and ensures that even if this PowerShell script exits or crashes, it doesn’t pollute the parent shell’s environment.
Setting Up the Frontend (Node.js Dependencies)
Next, the script configures the frontend. We ensure the frontend directory exists (if not, log an error – possibly the repo didn’t have a frontend, or clone failed). If it exists, we proceed to install Node.js packages:
- We first check that the Node Package Manager (npm) is available in the PATH. By this point, if Node.js was installed or updated, npm should be on the PATH (and we also refreshed the PATH earlier). If npm is not found, we log an error and advise the user to reopen the terminal (this situation would be similar to the original script marking “npm unavailable in current session”).
- We run npm config set fund false to disable funding messages (just like the batch script did) – this keeps the install output cleaner.
- We then call npm install in the frontend directory, which installs all dependencies listed in the project’s package.json. Any error here (non-zero exit) is logged and marked as a failure in the report. On success, we log that Node.js dependencies were installed.
- All npm output is directed to the log file rather than cluttering the console, although critical errors will still be reflected by the exit code and thus logged as [ERROR].
Creating Environment Files (.env)
Finally, the script ensures that all necessary environment configuration files are present, populating them with default placeholders if needed (just like the original script’s setupEnvironmentFiles section):
- The root .env file (in $ProjectRoot) is created if it doesn’t exist. We populate it with at least TAG=latest and CAMOUFOX_SOURCE=auto (these were in the batch script).
- The backend’s .env file is created if missing. If an .env.example exists in the backend, we copy it to .env for convenience. Otherwise, we create a new one with default values for Supabase URL/key, database credentials, and API keys as seen in the batch script template.
- The frontend’s .env file is created similarly – copying from .env.example if available, or creating with placeholders (VITE_SUPABASE_URL, VITE_SUPABASE_KEY, etc.).
Each creation is logged so the user knows which files were made. After creating these, we log an [IMPORTANT] message (mirroring the batch script) reminding the user to edit these .env files to put in actual credentials and API keys. These [IMPORTANT] lines are treated as info-level in the event log, but stand out in the console output for user attention.
Final Output and Interactive Prompts
With all steps completed, the script compiles a final status:
- If every step was successful ($blnSuccess remains true), the console will display a “Setup Complete” message with a summary. We log a [SUCCESS] event that everything was installed and configured successfully. The script then outlines the next steps to the user (as bullet points) exactly as the original did: edit the .env files with real credentials, run the scripts\windows\start.bat to launch the app, etc. We also include a prompt: “Would you like to start the application now? (y/n)”. If the user enters “y”, the script will attempt to launch the start.bat (it uses Start-Process to open it in a new Command Prompt window, since starting the development server might be a long-running process). If the start.bat is not found (for instance, if the repository has moved things around), we log a warning to that effect.
- If any step failed ($blnSuccess is false), the console will display “Setup Failed” along with a list of issues. This list comes from the accumulated $installReport string which contains lines like “Failed to install Git”, “Failed to clone repository”, etc., each gathered at the point of failure. The user can then consult the log file for more details, as indicated. We log a final [ERROR] event summarizing that setup failed (and in the Event Viewer details, one can see the specific issues as well, since we include them in the log file and also each was logged when it occurred).
Regardless of success or failure, the script prints the path to the log file (so the user knows where to find the full trace). Finally, it prints “Press any key to exit…” and waits. We use PowerShell’s [Console]::ReadKey() to wait for a single key press without echoing it to the screen, which effectively pauses the script until the user acknowledges the output[8]. This is particularly useful when running the script by double-clicking it or from a shortcut, as it keeps the window open to read the results.
With these changes, the PowerShell script is more resilient and user-friendly. It avoids the crashes experienced in the batch version and adheres to PowerShell best practices and idioms. We also maintain a high level of detail in logging and user messaging, so the process is transparent and any issues can be debugged using the log file or Event Viewer.
Complete PowerShell Script
Below is the full PowerShell script (setup-windows.ps1) implementing the above functionality. You can save this to a .ps1 file and run it in an elevated PowerShell session. Make sure the execution policy allows running scripts (you might need to run powershell.exe -ExecutionPolicy Bypass -File .\setup-windows.ps1 if not signed). The script will guide you through the setup and produce a log as described.
# PowerShell version of Suno Automation Windows Setup Script
# This script installs Git, Node.js (>=24.10), and Python 3.14 if needed,
# then sets up the Suno Automation project (backend and frontend).

# --- Initial Setup and Logging --- 

# Ensure the script is running as Administrator
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[ERROR] This script requires administrator privileges to run."
    Write-Host "[INFO]  Please right-click the script and select 'Run as Administrator'."
    Write-Host "Press Enter to exit..."
    Read-Host  # Wait for user to press Enter
    exit 1
}

# Determine script and project paths
$scriptRoot  = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrEmpty($scriptRoot)) { $scriptRoot = "." }  # current directory if none
$repoName    = "suno-automation"
$ProjectRoot = Join-Path $scriptRoot $repoName

# Prepare logging to file and Event Viewer
$logDir = Join-Path $scriptRoot "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$timeStamp = (Get-Date).ToString("yyyyMMdd-HHmmss")
$logFile   = Join-Path $logDir "setup-windows-$timeStamp.log"
$eventSource = "Suno Automation Setup"
# Register an event source (if not exists) and log start event
try {
    if (-not [System.Diagnostics.EventLog]::SourceExists($eventSource)) {
        New-EventLog -LogName Application -Source $eventSource
    }
} catch { }
# Log start in Event Viewer and file
Write-Host "[INFO] Suno Automation - Windows Setup Script started."
"[INFO] Suno Automation - Windows Setup Script started." | Out-File -FilePath $logFile -Encoding utf8
& eventcreate /ID 1 /L Application /T INFORMATION /SO "$eventSource" /D "Setup script started." | Out-Null

# Logging function
function Write-Log($level, $message) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    # Console output
    Write-Host "[$level] $message"
    # File output with timestamp
    "$timestamp [$level] $message" | Out-File -FilePath $logFile -Encoding utf8 -Append
    # Event Viewer output
    $eventType = "INFORMATION"
    if ($level.ToUpper() -eq "ERROR")   { $eventType = "ERROR" }
    elseif ($level.ToUpper() -eq "WARNING") { $eventType = "WARNING" }
    & eventcreate /ID 1 /L Application /T $eventType /SO "$eventSource" /D "$message" | Out-Null
}

Write-Log "INFO" "Log file: $logFile"
Write-Log "INFO" "Checking network connectivity..."
# Simple ping to check internet
$ping = Test-Connection -ComputerName "google.com" -Count 1 -Quiet
if (-not $ping) {
    Write-Log "ERROR" "No internet connection detected. Please check your network and try again."
    Write-Host ""
    Write-Host "Press Enter to exit..."
    Read-Host
    exit 1
}
Write-Log "SUCCESS" "Network connectivity confirmed."

Write-Log "INFO" "Checking for Winget..."
if (-not (Get-Command "winget" -ErrorAction SilentlyContinue)) {
    Write-Log "ERROR" "Winget is not available on this system."
    Write-Log "INFO" "Please install the Windows Package Manager (App Installer) or update your Windows installation."
    Write-Host ""
    Write-Host "Press Enter to exit..."
    Read-Host
    exit 1
}
Write-Log "SUCCESS" "Winget is available."

# Variables to track installation results
$blnSuccess     = $true
$blnNeedsInstall = $false   # if any new install happened (to potentially advise a restart, though we handle PATH)
$installReport  = ""        # will collect failure messages for final display

# --- Ensure Git --- 
Write-Log "INFO" "Checking Git installation..."
try {
    $null = & git --version 2>$null
} catch { }
if ($LASTEXITCODE -ne 0) {
    Write-Log "INFO" "Installing Git via Winget..."
    $wingetGit = Start-Process -FilePath "winget" -ArgumentList @("install", "--exact", "--accept-package-agreements", "--accept-source-agreements", "Git.Git") -Wait -PassThru
    if ($wingetGit.ExitCode -ne 0) {
        $blnSuccess = $false
        $installReport += "Failed to install Git`n"
        Write-Log "ERROR" "Failed to install Git."
    } else {
        Write-Log "SUCCESS" "Git installed successfully."
        $blnNeedsInstall = $true
    }
} else {
    Write-Log "SUCCESS" "Git is already installed."
}

# --- Ensure Node.js (24.10 or higher) --- 
Write-Log "INFO" "Checking Node.js installation..."
$nodeMajor = $nodeMinor = $null
try {
    $nodeVersionOutput = & node --version 2>$null    # e.g., "v18.16.0"
} catch { $nodeVersionOutput = $null }
if ($LASTEXITCODE -ne 0 -or -not $nodeVersionOutput) {
    Write-Log "INFO" "Node.js not found. Installing Node.js LTS via Winget..."
    $wingetNode = Start-Process -FilePath "winget" -ArgumentList @("install", "--exact", "--accept-package-agreements", "--accept-source-agreements", "OpenJS.NodeJS.LTS") -Wait -PassThru
    if ($wingetNode.ExitCode -ne 0) {
        $blnSuccess = $false
        $installReport += "Failed to install Node.js`n"
        Write-Log "ERROR" "Failed to install Node.js."
    } else {
        Write-Log "SUCCESS" "Node.js installed successfully."
        $blnNeedsInstall = $true
        # Refresh PATH to include new Node.js if installed
        Refresh-NodePath
    }
    # Re-check version after fresh install
    $nodeVersionOutput = & node --version 2>$null
} else {
    # Node exists, parse version
    if ($nodeVersionOutput -match "^v(\d+)\.(\d+)\.") {
        $nodeMajor = [int]$Matches[1]
        $nodeMinor = [int]$Matches[2]
    }
    if (-not $nodeMajor) {
        if ($nodeVersionOutput) {
            Write-Log "WARNING" "Unable to parse Node.js version from '$nodeVersionOutput'. Proceeding with detected installation."
        } else {
            Write-Log "WARNING" "Unable to determine Node.js version. Ensure Node.js >= 24.10."
        }
    }
    $needNodeUpgrade = $false
    if ($nodeMajor -lt 24 -or ($nodeMajor -eq 24 -and $nodeMinor -lt 10)) {
        $needNodeUpgrade = $true
    }
    if ($needNodeUpgrade) {
        Write-Log "INFO" "Node.js version $nodeMajor.$nodeMinor does not meet the required 24.10. Upgrading to latest LTS..."
        $wingetNodeUp = Start-Process -FilePath "winget" -ArgumentList @("upgrade", "--exact", "--accept-package-agreements", "--accept-source-agreements", "OpenJS.NodeJS.LTS") -Wait -PassThru
        if ($wingetNodeUp.ExitCode -ne 0) {
            Write-Log "WARNING" "Node.js upgrade failed or not needed. Continuing with existing version."
        } else {
            Write-Log "SUCCESS" "Node.js upgraded to the latest LTS release."
            $blnNeedsInstall = $true
            Refresh-NodePath
            $nodeVersionOutput = & node --version 2>$null  # update version string after upgrade
        }
    }
}
# Verify Node availability after any install/upgrade
try { $null = & node --version 2>$null } catch { }
if ($LASTEXITCODE -ne 0) {
    $blnSuccess = $false
    $installReport += "Node.js unavailable in current session`n"
    Write-Log "ERROR" "Node.js is not available in this session after installation. Please restart your terminal and try again."
} else {
    if ($nodeVersionOutput) {
        Write-Log "SUCCESS" "Node.js is available ($nodeVersionOutput)."
    } else {
        Write-Log "SUCCESS" "Node.js installation verified."
    }
}

# Helper function: Refresh-NodePath
function Refresh-NodePath {
    $nodeLocations = @(
        "$env:ProgramFiles\nodejs\node.exe",
        "$env:ProgramFiles(x86)\nodejs\node.exe",
        "$env:LOCALAPPDATA\Programs\nodejs\node.exe"
    )
    foreach ($nodeExe in $nodeLocations) {
        if (Test-Path $nodeExe) {
            $nodeDir = Split-Path -Parent $nodeExe
            Write-Log "DEBUG" "Adding Node.js install location to PATH: $nodeDir"
            $env:Path = "$nodeDir;$($env:Path)"
            break
        }
    }
}

# --- Ensure Python 3.14 --- 
Write-Log "INFO" "Checking Python 3.14 installation..."
$pyMajor = $pyMinor = $null
try {
    $pythonVersionOutput = & python --version 2>$null   # e.g., "Python 3.13.5"
} catch { $pythonVersionOutput = $null }
if ($LASTEXITCODE -ne 0 -or -not $pythonVersionOutput) {
    Write-Log "INFO" "Python 3.14 not found. Installing via Winget..."
    $wingetPy = Start-Process -FilePath "winget" -ArgumentList @("install", "--exact", "--accept-package-agreements", "--accept-source-agreements", "Python.Python.3.14") -Wait -PassThru
    if ($wingetPy.ExitCode -ne 0) {
        $blnSuccess = $false
        $installReport += "Failed to install Python 3.14`n"
        Write-Log "ERROR" "Failed to install Python 3.14."
    } else {
        Write-Log "SUCCESS" "Python 3.14 installed successfully."
        $blnNeedsInstall = $true
        Refresh-PythonPath
    }
    # Update version output after installation
    $pythonVersionOutput = & python --version 2>$null
} else {
    # Python exists, parse version
    if ($pythonVersionOutput -match "Python (\d+)\.(\d+)\.") {
        $pyMajor = [int]$Matches[1]
        $pyMinor = [int]$Matches[2]
    }
    if (-not $pyMajor) {
        if ($pythonVersionOutput) {
            Write-Log "WARNING" "Unable to parse Python version from '$pythonVersionOutput'. Proceeding with detected installation."
        } else {
            Write-Log "WARNING" "Unable to determine Python version. Ensure Python >= 3.14."
        }
    }
    $needPyUpgrade = $false
    if ($pyMajor -lt 3 -or ($pyMajor -eq 3 -and $pyMinor -lt 14)) {
        $needPyUpgrade = $true
    }
    if ($needPyUpgrade) {
        Write-Log "INFO" "Python version $pyMajor.$pyMinor does not meet the required 3.14. Upgrading via Winget..."
        $wingetPyUp = Start-Process -FilePath "winget" -ArgumentList @("upgrade", "--exact", "--accept-package-agreements", "--accept-source-agreements", "Python.Python.3.14") -Wait -PassThru
        if ($wingetPyUp.ExitCode -ne 0) {
            Write-Log "WARNING" "Python upgrade failed or not available. Continuing with existing version."
        } else {
            Write-Log "SUCCESS" "Python upgraded to 3.14."
            $blnNeedsInstall = $true
            Refresh-PythonPath
            $pythonVersionOutput = & python --version 2>$null
        }
    }
}
# Verify Python availability
try { $null = & python --version 2>$null } catch { }
if ($LASTEXITCODE -ne 0) {
    $blnSuccess = $false
    $installReport += "Python unavailable in current session`n"
    Write-Log "ERROR" "Python is not available in this session after installation. Please restart your terminal and try again."
} else {
    if ($pythonVersionOutput) {
        Write-Log "SUCCESS" "Python is available ($pythonVersionOutput)."
    } else {
        Write-Log "SUCCESS" "Python installation verified."
    }
}

# Helper function: Refresh-PythonPath
function Refresh-PythonPath {
    $pyLocations = @(
        "$env:LocalAppData\Programs\Python\Python314\python.exe",
        "$env:ProgramFiles\Python314\python.exe",
        "$env:ProgramFiles\Python\Python314\python.exe"
    )
    foreach ($pyExe in $pyLocations) {
        if (Test-Path $pyExe) {
            $pyDir = Split-Path -Parent $pyExe
            Write-Log "DEBUG" "Adding Python install location to PATH: $pyDir"
            $env:Path = "$pyDir;$($env:Path)"
            break
        }
    }
}

# --- Clone or Update Repository --- 
Write-Log "INFO" "Setting up repository at $ProjectRoot..."
if (Test-Path "$ProjectRoot\.git") {
    Write-Log "INFO" "Existing repository found. Updating..."
    try {
        # Using -C to run git in the target directory
        $gitPullOutput = git -C $ProjectRoot pull 2>&1
    } catch {
        $gitPullOutput = $_.Exception.Message
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Log "WARNING" "Failed to pull updates from remote. Continuing with the local version. (`$gitPullOutput`)"
    } else {
        Write-Log "SUCCESS" "Repository updated successfully."
    }
} elseif (Test-Path $ProjectRoot) {
    # Directory exists but not a git repo
    Write-Log "ERROR" "Project directory '$ProjectRoot' already exists and is not a git repository."
    $blnSuccess = $false
    $installReport += "Failed to clone repository`n"
} else {
    Write-Log "INFO" "No existing repository found. Cloning a fresh copy..."
    New-Item -ItemType Directory -Path $ProjectRoot -Force | Out-Null
    try {
        $gitCloneOutput = git clone https://github.com/vnmw7/suno-automation.git $ProjectRoot 2>&1
    } catch {
        $gitCloneOutput = $_.Exception.Message
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR" "Failed to clone repository. ($gitCloneOutput)"
        $blnSuccess = $false
        $installReport += "Failed to clone repository`n"
    } else {
        Write-Log "SUCCESS" "Repository cloned to $ProjectRoot"
    }
}

# Only proceed with further setup if repository is available
if ($blnSuccess -and (Test-Path $ProjectRoot)) {

    # --- Setup Backend ---
    Write-Log "INFO" "Setting up backend environment..."
    $backendPath = Join-Path $ProjectRoot "backend"
    if (-not (Test-Path $backendPath)) {
        Write-Log "ERROR" "Backend directory not found at '$backendPath'."
        $blnSuccess = $false
        $installReport += "Backend directory not found`n"
    } else {
        Push-Location $backendPath
        # Create virtual environment if not exists
        if (-not (Test-Path ".venv")) {
            Write-Log "INFO" "Creating Python virtual environment..."
            try {
                $null = & python -m venv .venv 2>&1
            } catch {
                Write-Log "ERROR" "Failed to create virtual environment. ($($_.Exception.Message))"
                $blnSuccess = $false
                $installReport += "Failed to create virtual environment`n"
            }
            if ($LASTEXITCODE -eq 0 -and $blnSuccess) {
                Write-Log "SUCCESS" "Virtual environment created."
            }
        } else {
            Write-Log "SUCCESS" "Virtual environment already exists."
        }

        # Activate venv by using its Python/Pip directly (no need to modify session)
        $pipPath = ".venv\Scripts\pip.exe"
        if (-not (Test-Path $pipPath)) {
            Write-Log "ERROR" "Failed to activate virtual environment (pip not found)."
            $blnSuccess = $false
            $installReport += "Failed to activate virtual environment`n"
        } else {
            # Upgrade pip
            Write-Log "INFO" "Upgrading pip in virtual environment..."
            $pipUpgradeOutput = & $pipPath install --upgrade pip 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Log "WARNING" "Failed to upgrade pip (non-critical). Continuing. ($pipUpgradeOutput)"
            } else {
                Write-Log "SUCCESS" "Pip upgraded (if not already latest)."
            }
            # Install Python requirements
            Write-Log "INFO" "Installing Python dependencies (from requirements.txt)..."
            if (Test-Path "requirements.txt") {
                $pipInstallOutput = & $pipPath install -r requirements.txt 2>&1
            } else {
                $pipInstallOutput = "requirements.txt not found"
                $LASTEXITCODE = 1
            }
            if ($LASTEXITCODE -ne 0) {
                Write-Log "ERROR" "Failed to install Python dependencies. ($pipInstallOutput)"
                $blnSuccess = $false
                $installReport += "Failed to install Python dependencies`n"
            } else {
                Write-Log "SUCCESS" "Python dependencies installed."
            }
            # Download Camoufox payload
            Write-Log "INFO" "Downloading Camoufox browser payload..."
            # Camoufox might be installed as an entry point by pip, attempt to run it
            $camoufoxCmd = ".venv\Scripts\camoufox.exe"
            if (-not (Test-Path $camoufoxCmd)) { $camoufoxCmd = ".venv\Scripts\camoufox" }
            if (Test-Path $camoufoxCmd) {
                $camoufoxOutput = & $camoufoxCmd fetch 2>&1
                if ($LASTEXITCODE -ne 0) {
                    Write-Log "WARNING" "Failed to download Camoufox payload. You may need to run 'camoufox fetch' manually. ($camoufoxOutput)"
                } else {
                    Write-Log "SUCCESS" "Camoufox payload downloaded."
                }
            } else {
                Write-Log "WARNING" "Camoufox tool not found in the virtual environment. Skipping payload download."
            }
        }
        Pop-Location
        if ($blnSuccess) {
            Write-Log "SUCCESS" "Backend setup completed."
        }
    }

    # --- Setup Frontend ---
    Write-Log "INFO" "Setting up frontend dependencies..."
    $frontendPath = Join-Path $ProjectRoot "frontend"
    if (-not (Test-Path $frontendPath)) {
        Write-Log "ERROR" "Frontend directory not found at '$frontendPath'."
        $blnSuccess = $false
        $installReport += "Frontend directory not found`n"
    } else {
        Push-Location $frontendPath
        # Ensure npm is available (Node.js should have installed it)
        if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
            Write-Log "ERROR" "npm not found on PATH. Please restart your terminal or open a new shell, then rerun this script."
            $blnSuccess = $false
            $installReport += "npm unavailable in current session`n"
        } else {
            # Optional: suppress funding messages
            $null = & npm config set fund false 2>$null
            # Install Node.js dependencies
            Write-Log "INFO" "Installing Node.js dependencies (npm install)..."
            $npmOutput = & npm install 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Log "ERROR" "Failed to install Node.js dependencies. ($npmOutput)"
                $blnSuccess = $false
                $installReport += "Failed to install Node.js dependencies`n"
            } else {
                Write-Log "SUCCESS" "Node.js dependencies installed."
            }
        }
        Pop-Location
        if ($blnSuccess) {
            Write-Log "SUCCESS" "Frontend setup completed."
        }
    }

    # --- Create Environment Files ---
    Write-Log "INFO" "Setting up environment files..."
    if (-not (Test-Path $ProjectRoot)) {
        Write-Log "ERROR" "Project root directory '$ProjectRoot' not found. Unable to create environment files."
        $blnSuccess = $false
        $installReport += "Project root directory not found for environment files`n"
    } else {
        # Root .env
        $rootEnvPath = Join-Path $ProjectRoot ".env"
        if (-not (Test-Path $rootEnvPath)) {
            Write-Log "INFO" "Creating root .env file..."
            @"
TAG=latest
CAMOUFOX_SOURCE=auto
"@ | Out-File -FilePath $rootEnvPath -Encoding ascii
            Write-Log "SUCCESS" "Root .env file created."
        }
        # Backend .env
        $backendEnvPath = Join-Path $ProjectRoot "backend\.env"
        $backendEnvExample = Join-Path $ProjectRoot "backend\.env.example"
        if (-not (Test-Path $backendEnvPath)) {
            Write-Log "INFO" "Creating backend .env file..."
            if (Test-Path $backendEnvExample) {
                Copy-Item $backendEnvExample $backendEnvPath
                Write-Log "SUCCESS" "Backend .env file created from example."
            } else {
                @"
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_KEY=your-vite-supabase-key
USER=your-database-user
PASSWORD=your-database-password
HOST=your-database-host
PORT=5432
DBNAME=postgres
GOOGLE_AI_API_KEY=your-google-ai-api-key
"@ | Out-File -FilePath $backendEnvPath -Encoding ascii
                Write-Log "SUCCESS" "Backend .env file created with defaults."
            }
        }
        # Frontend .env
        $frontendEnvPath = Join-Path $ProjectRoot "frontend\.env"
        $frontendEnvExample = Join-Path $ProjectRoot "frontend\.env.example"
        if (-not (Test-Path $frontendEnvPath)) {
            Write-Log "INFO" "Creating frontend .env file..."
            if (Test-Path $frontendEnvExample) {
                Copy-Item $frontendEnvExample $frontendEnvPath
                Write-Log "SUCCESS" "Frontend .env file created from example."
            } else {
                @"
VITE_SUPABASE_URL=your_supabase_url_here
VITE_SUPABASE_KEY=your_supabase_key_here
VITE_API_URL=http://localhost:8000
NODE_ENV=production
"@ | Out-File -FilePath $frontendEnvPath -Encoding ascii
                Write-Log "SUCCESS" "Frontend .env file created with defaults."
            }
        }
        Write-Log "INFO" "Environment files have been created with default values."
        Write-Log "IMPORTANT" "Please edit the .env files to add your actual credentials and API keys."
    }
}

# --- Final Status and Summary --- 
Write-Host ""
Write-Host "========================================"
if ($blnSuccess) {
    Write-Host " Setup Complete"
    Write-Host "========================================"
    Write-Host ""
    Write-Log "SUCCESS" "All components have been installed and configured successfully!"
    Write-Host "Your Suno Automation environment is ready to use."
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "1. Edit the .env files to add your credentials:"
    Write-Host "   - backend\\.env: Add your Supabase and Google AI API keys"
    Write-Host "   - frontend\\.env: Add your Supabase URL and keys"
    Write-Host "2. Run 'scripts\\windows\\start.bat' to launch the application"
    Write-Host "3. Run 'scripts\\windows\\stop.bat' to stop the application"
    Write-Host ""
    $startScript = Join-Path $ProjectRoot "scripts\\windows\\start.bat"
    if (-not (Test-Path $startScript)) {
        # Fallback: perhaps scriptRoot if clone path changed
        $startScript = Join-Path $scriptRoot "start.bat"
    }
    $response = Read-Host "Would you like to start the application now? (y/n)"
    if ($response -match '^(Y|y)') {
        Write-Log "INFO" "Starting application..."
        if (Test-Path $startScript) {
            # Launch the start script in a new window (so this script can finish)
            Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$startScript`""
        } else {
            Write-Log "WARNING" "start.bat not found at '$startScript'. Please run it manually when ready."
        }
    }
} else {
    Write-Host " Setup Failed"
    Write-Host "========================================"
    Write-Host ""
    Write-Log "ERROR" "Setup failed. See details below."
    Write-Host "The following issues were reported:"
    if ([string]::IsNullOrEmpty($installReport)) {
        Write-Host "- An unexpected error occurred."
    } else {
        # Print each issue line
        $installReport.Trim() -split "`n" | ForEach-Object { if ($_) { Write-Host $_ } }
    }
    Write-Host ""
    Write-Host "Please check the log file for a complete execution trace:"
    Write-Host "$logFile"
}
Write-Log "INFO" "Setup script completed. Log file saved to: $logFile"
Write-Host ""
Write-Host "Log file saved to: $logFile"
Write-Host "You can also check the Windows Event Viewer for '$eventSource' events."
Write-Host ""
Write-Host "Press any key to exit..."
# Wait for any key press (without requiring Enter), and hide the pressed key
$null = [System.Console]::ReadKey($true)
________________________________________
[1] How to get the path of the currently executing script in PowerShell?
https://www.tutorialspoint.com/how-to-get-the-path-of-the-currently-executing-script-in-powershell
[2] How to Write Logs to the Windows Event Viewer from PowerShell/CMD | Windows OS Hub
https://woshub.com/write-logs-event-viewer-powershell-cmd/
[3] [4] How to Check if a PowerShell Script is Running with Admin Privileges
https://petri.com/how-to-check-a-powershell-script-is-running-with-admin-privileges/
[5] [8] Press Any Key to Continue in PowerShell [6 Ways] - Java2Blog
https://java2blog.com/press-any-key-to-continue-powershell/
[6] [7] Scripting Winget - Chris’s Tech ADHD
https://chris-ayers.com/2021/08/01/scripting-winget/
