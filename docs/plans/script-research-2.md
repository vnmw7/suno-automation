# Suno Automation PowerShell Setup Script

---
## Overview
This PowerShell script automates environment provisioning for the Suno Automation project when executed from ANY external drive or folder. It installs and configures Git, Node.js (24.10+), and Python 3.14 if not present or outdated, and replicates existing robust logging:
- Log to file in ./logs and to Windows Event Viewer
- Mimics `setup-windows.bat` menus and interactive prompts

**Portable execution, context-resilient:** All paths and operations auto-adjust to the script's own location for maximum portability.

---
## PowerShell Script — setup-sunoautomation.ps1
```powershell
<#
.SYNOPSIS
Portable & interactive bootstrap for Suno Automation environment
#>

### --- Initialization --- ###
$ErrorActionPreference = 'Stop'
$scriptRoot = $PSScriptRoot
if (-not $scriptRoot) { $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path }
$logDir = Join-Path $scriptRoot 'logs'
if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
$logFile = Join-Path $logDir ("windows-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".log")
$eventSource = 'Suno Automation Setup'
$global:success = $true
$global:installReport = ""

function Write-Log {
    param (
        [string]$Message,
        [ValidateSet("INFO", "WARNING", "ERROR", "SUCCESS", "DEBUG")][string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $msgText = "$timestamp [$Level] $Message"
    Add-Content -Path $logFile -Value $msgText
    Write-Host $msgText -ForegroundColor (
        switch ($Level) {
            "INFO" { "White" }
            "WARNING" { "Yellow" }
            "ERROR" { "Red" }
            "SUCCESS" { "Green" }
            "DEBUG" { "Magenta" }
        }
    )
    # Event Viewer log
    Try {
        if (!(Get-EventLog -LogName 'Application' -Source $eventSource -ErrorAction SilentlyContinue)) {
            New-EventLog -LogName 'Application' -Source $eventSource
        }
        $eventType = switch ($Level) { "INFO" { "Information" }; "WARNING" { "Warning" }; "ERROR" { "Error" }; default { "Information" } }
        Write-EventLog -LogName 'Application' -Source $eventSource -EventId 3002 -EntryType $eventType -Message $Message
    } Catch {} # suppress errors if not running elevated
}

Write-Log "Suno Automation PowerShell Setup Script started." "INFO"
Write-Log "Log file: $logFile" "INFO"

### --- Prerequisite Checks --- ###
function Ensure-Admin {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Log "This script requires administrator privileges for installing software." "ERROR"
        Write-Log "Please right-click this script and select 'Run as administrator.'" "INFO"
        Pause
        exit 1
    }
}
Ensure-Admin

function Test-Network {
    Write-Log "Checking network connectivity..." "INFO"
    Try {
        $res = Test-Connection -ComputerName 'google.com' -Count 1 -Quiet
        if ($res) {
            Write-Log "Network connectivity confirmed." "SUCCESS"
        } else {
            Write-Log "No internet connection detected. Please check your network and try again." "ERROR"
            Pause
            exit 1
        }
    } Catch {
        Write-Log "Network check failed: $_" "ERROR"
        Pause
        exit 1
    }
}
Test-Network

function Test-Winget {
    Write-Log "Checking for Winget..." "INFO"
    Try {
        winget --version | Out-Null
        Write-Log "Winget is available." "SUCCESS"
    } Catch {
        Write-Log "Winget is not available on this system." "ERROR"
        Write-Log "Please install Windows Package Manager or update your Windows 10/11 installation." "INFO"
        Pause
        exit 1
    }
}
Test-Winget

### --- Tool Installation --- ###
function Ensure-Git {
    Write-Log "Checking Git installation..." "INFO"
    $git = Get-Command git -ErrorAction SilentlyContinue
    if (!$git) {
        Write-Log "Installing Git via Winget..." "INFO"
        Try {
            winget install --exact --accept-package-agreements --accept-source-agreements Git.Git
            Write-Log "Git installed successfully." "SUCCESS"
        } Catch {
            Write-Log "Failed to install Git." "ERROR"
            $global:success = $false
            $global:installReport += "Failed to install Git. "$($_.Exception.Message)
        }
    } else {
        Write-Log "Git is already installed. Version: $(git --version)" "SUCCESS"
    }
}
Ensure-Git

function Ensure-Node {
    Write-Log "Checking Node.js installation..." "INFO"
    $nodever = $null
    Try { $nodever = node -v } Catch {}
    if ($nodever) {
        $match = $nodever -match '^v(\d+)\.(\d+)'
        $major = [int]$Matches[1]; $minor = [int]$Matches[2]
        if ($major -lt 24 -or ($major -eq 24 -and $minor -lt 10)) {
            Write-Log "Node.js version $major.$minor does not meet the required 24.10+. Upgrading..." "INFO"
            Try {
                winget install --exact --accept-package-agreements --accept-source-agreements OpenJS.NodeJS.LTS
                Write-Log "Node.js upgraded to the latest LTS release." "SUCCESS"
            } Catch {
                Write-Log "Failed to install Node.js." "ERROR"
                $global:success = $false
                $global:installReport += "Failed to install Node.js. "$($_.Exception.Message)
            }
        } else {
            Write-Log "Node.js is available $nodever" "SUCCESS"
        }
    } else {
        Write-Log "Node.js not found. Installing..." "INFO"
        Try {
            winget install --exact --accept-package-agreements --accept-source-agreements OpenJS.NodeJS.LTS
            Write-Log "Node.js installed successfully." "SUCCESS"
        } Catch {
            Write-Log "Failed to install Node.js." "ERROR"
            $global:success = $false
            $global:installReport += "Failed to install Node.js. "$($_.Exception.Message)
        }
    }
}
Ensure-Node

function Ensure-Python {
    Write-Log "Checking Python installation..." "INFO"
    $pythonver = $null
    Try { $pythonver = python --version 2>&1 } Catch { $pythonver = $null }
    if ($pythonver) {
        $match = $pythonver -match 'Python (\d+)\.(\d+)' 
        $major = [int]$Matches[1]; $minor = [int]$Matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 14)) {
            Write-Log "Python version $major.$minor does not meet the required 3.14. Upgrading..." "INFO"
            Try {
                winget install --exact --accept-package-agreements --accept-source-agreements Python.Python.3.14
                Write-Log "Python 3.14 installed successfully." "SUCCESS"
            } Catch {
                Write-Log "Failed to install Python 3.14." "ERROR"
                $global:success = $false
                $global:installReport += "Failed to install Python. "$($_.Exception.Message)
            }
        } else {
            Write-Log "Python is available: $pythonver" "SUCCESS"
        }
    } else {
        Write-Log "Python not found. Installing..." "INFO"
        Try {
            winget install --exact --accept-package-agreements --accept-source-agreements Python.Python.3.14
            Write-Log "Python 3.14 installed successfully." "SUCCESS"
        } Catch {
            Write-Log "Failed to install Python 3.14." "ERROR"
            $global:success = $false
            $global:installReport += "Failed to install Python. "$($_.Exception.Message)
        }
    }
}
Ensure-Python

### --- Repository Setup --- ###
$repoUrl = "https://github.com/vnmw7/suno-automation.git"
$repoName = "suno-automation"
$projectRoot = Join-Path $scriptRoot $repoName
if (!(Test-Path $projectRoot)) {
    Write-Log "No existing repository found. Cloning a fresh copy..." "INFO"
    Try {
        git clone $repoUrl $projectRoot
        Write-Log "Repository cloned to $projectRoot" "SUCCESS"
    } Catch {
        Write-Log "Failed to clone repository: $_" "ERROR"
        $global:success = $false
        $global:installReport += "Failed to clone repository. "$($_.Exception.Message)
    }
} else {
    Write-Log "Existing repository found. Updating..." "INFO"
    Try {
        Push-Location $projectRoot
        git pull
        Pop-Location
        Write-Log "Repository updated successfully." "SUCCESS"
    } Catch {
        Write-Log "Failed to update repository: $_" "WARNING"
    }
}

### --- Environment Setup --- ###
# Backend: Python venv + dependencies
$backendDir = $projectRoot
Push-Location $backendDir
if (!(Test-Path ".venv")) {
    Write-Log "Creating Python virtual environment..." "INFO"
    Try {
        python -m venv .venv
        Write-Log "Virtual environment created." "SUCCESS"
    } Catch {
        Write-Log "Failed to create virtual environment: $_" "ERROR"
        $global:success = $false
        $global:installReport += "Failed to create Python venv. "$($_.Exception.Message)
    }
}
Write-Log "Activating virtual environment..." "INFO"
$venvActivate = Join-Path $backendDir ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
}
Write-Log "Upgrading pip..." "INFO"
python -m pip install --upgrade pip
Write-Log "Installing Python dependencies..." "INFO"
if (Test-Path "requirements.txt") {
    Try {
        pip install -r requirements.txt
        Write-Log "Python dependencies installed." "SUCCESS"
    } Catch {
        Write-Log "Failed to install Python dependencies." "ERROR"
        $global:success = $false
        $global:installReport += "Failed to install Python dependencies. "$($_.Exception.Message)
    }
} else {
    Write-Log "No requirements.txt found in backend directory." "WARNING"
}
Pop-Location

# Frontend: Node.js dependencies
Push-Location $projectRoot
if (Test-Path "package.json") {
    Write-Log "Installing Node.js dependencies..." "INFO"
    Try {
        npm config set fund false
        npm install
        Write-Log "Node.js dependencies installed." "SUCCESS"
    } Catch {
        Write-Log "Failed to install Node.js dependencies." "ERROR"
        $global:success = $false
        $global:installReport += "Failed to install Node.js dependencies. "$($_.Exception.Message)
    }
} else {
    Write-Log "No package.json found. Skipping frontend setup." "WARNING"
}
Pop-Location

### --- Environment Files Provisioning --- ###
function Ensure-EnvFiles {
    param([string]$targetPath)
    Write-Log "Setting up environment files..." "INFO"
    $envFile = Join-Path $targetPath ".env"
    if (!(Test-Path $envFile)) {
        Set-Content $envFile "TAG=latest`nCAMOUFOXSOURCE=auto"
        Write-Log "Root .env file created." "SUCCESS"
    }
}
Ensure-EnvFiles $projectRoot
Ensure-EnvFiles (Join-Path $projectRoot "backend")
Ensure-EnvFiles (Join-Path $projectRoot "frontend")
Write-Log "IMPORTANT: Please edit the .env files to add your credentials and API keys." "INFO"

### --- Final Status & Interactive Menu --- ###
function Display-FinalStatus {
    Write-Host "\n\n==== Setup Complete ===="
    if ($global:success) {
        Write-Log "All components have been installed and configured successfully!" "SUCCESS"
        Write-Host "Your Suno Automation environment is ready to use."
    } else {
        Write-Log "Setup failed. See details below." "ERROR"
        Write-Host "\nSetup Failed."
        if ($global:installReport) {
            Write-Host $global:installReport
        } else {
            Write-Host "- An unexpected error occurred."
        }
    }
    Write-Host "\nLog file saved to: $logFile"
    Write-Host "You can also check the Windows Event Viewer (Application log, Source: '$eventSource') for Suno Automation Setup events."
}
Display-FinalStatus

function Show-Menu {
    param ([string]$Title = 'Suno Automation Setup')
    Clear-Host
    Write-Host " =========== $Title =========== "
    Write-Host "[1] Edit .env files to add credentials and API keys."
    Write-Host "[2] Launch the backend (Python) server."
    Write-Host "[3] Launch the frontend (Node.js) application."
    Write-Host "[Q] Quit."
}

Do {
    Show-Menu
    $choice = Read-Host "Please select an option"
    Switch ($choice.ToUpper()) {
        '1' { Write-Host "Please edit $projectRoot\.env and corresponding backend/frontend .env files." }
        '2' {
            Write-Log "Starting backend application..." "INFO"
            Push-Location $projectRoot
            & python main.py
            Pop-Location
        }
        '3' {
            Write-Log "Starting frontend application..." "INFO"
            Push-Location $projectRoot
            & npm start
            Pop-Location
        }
        'Q' { Write-Log "Exiting interactive menu..." "INFO" }
        Default { Write-Host "Invalid selection. Please choose again." }
    }
} Until ($choice.ToUpper() -eq 'Q')

Write-Host "Press any key to exit..."; [void][System.Console]::ReadKey($true)
Write-Log "Suno Automation PowerShell Setup completed." "INFO"
```

---
## Usage & Notes
- **Run directly from any external or local drive.**
- **Administrator privileges required for installs.**
- All logs written in ./logs next to the script and to Windows Event Viewer (Application log).
- If installation steps fail, check both log and Event Viewer for troubleshooting.
- All paths and repo clones use the script's own folder for maximal portability.

---
**Menu system and interactive prompts at the end mirror the original batch script, allowing further manual setup, launches, or troubleshooting.**

**This script uses best practices for robust, portable, and secure Windows automation in PowerShell as of October 2025.**

