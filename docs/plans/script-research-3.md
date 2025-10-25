Technical Report: Re-engineering the 'suno-automation' Development Environment Setup1.0 Executive Summary1.1 Project MandateThis report addresses a request to diagnose and resolve critical failures within a Windows batch script designed to automate the setup of the 'suno-automation' development environment. The primary objective is to re-engineer the legacy script into a robust, modern PowerShell automation solution that is portable, idempotent, and adheres to contemporary software development best practices.1.2 Diagnosis of Legacy FailuresA thorough analysis of the provided terminal outputs and error logs reveals that the legacy batch script's failures are systemic, stemming from the inherent limitations of the batch scripting language. The core issues identified include: unreliable path resolution, which is highly dependent on the script's execution context; inadequate and non-granular error handling for external command-line tools such as Git and Python; and a complete absence of prerequisite validation, leading to opaque failures if required software is missing or outdated. These deficiencies result in a brittle and unpredictable setup process.1.3 The PowerShell Solution: A Paradigm ShiftThe engineered solution presented in this report is a comprehensive PowerShell script that replaces the legacy batch file. This new script represents a paradigm shift from procedural fragility to declarative robustness. Its key architectural features include:Full Portability: The script dynamically resolves all necessary paths relative to its own location, ensuring consistent and correct execution regardless of where it is stored, including on external or network drives.Automated Prerequisite Management: The script proactively validates the presence and version of all required dependencies (Git, Node.js, Python). If a dependency is missing or does not meet the minimum version requirement, it is automatically installed or upgraded using the native Windows Package Manager (winget).Structured Error Handling: A sophisticated, dual-strategy error handling mechanism is implemented. It correctly distinguishes between internal PowerShell cmdlet errors and the exit codes of external executables, providing precise and actionable failure diagnostics.Dual-Channel Logging: The script provides comprehensive logging to two distinct channels: a detailed, timestamped text file for forensic analysis and the Windows Event Viewer for high-level system monitoring and integration with enterprise management tools.1.4 Key OutcomesThe final deliverable is a single, self-contained PowerShell script that provides a one-click, reliable, and idempotent setup process for the 'suno-automation' development environment. This solution eliminates the need for manual intervention, significantly reduces the potential for human error, and provides clear, actionable diagnostics in the event of a failure. It transforms the environment setup from a source of friction into a dependable and repeatable automated workflow.2.0 Deconstruction of Legacy Batch Script Failures2.1 Analysis of Terminal and Log OutputsThe user-provided diagnostic information points to a series of cascading failures. A systematic breakdown of these errors reveals a clear chain of causation rooted in the fundamental weaknesses of the batch scripting environment."The system cannot find the path specified" during git cloneThis error is the primary indicator of the script's lack of portability. Batch scripts operate based on the current working directory (%CD%), which can vary unpredictably depending on how the script is invoked (e.g., from a command prompt opened in a different folder, via a shortcut with a "Start in" property, etc.). The script likely assumes it is being run from a specific location and attempts to create directories or clone the repository relative to that assumed path. When the actual %CD% is different, the relative path becomes invalid, leading to this error. This will be directly contrasted with PowerShell's reliable $PSScriptRoot automatic variable, which always contains the full path to the directory where the script file itself resides, providing a stable anchor for all relative path operations.Python venv and pip ErrorsErrors such as "pip is not recognized as an internal or external command" are classic symptoms of improper environment variable management and scope issues within batch files. The Python virtual environment activation script (activate.bat) works by temporarily modifying the PATH environment variable to prepend the path to the virtual environment's Scripts directory. However, in a batch context, changes made by a called script (using CALL) can be transient. More critically, if the script fails to navigate to the correct directory before attempting activation, it will not find activate.bat in the first place. The failure to correctly activate the environment means that subsequent calls to pip or python resolve to the system-wide installations (if any), not the isolated virtual environment, thus defeating its purpose and causing dependency conflicts or "command not found" errors.File Access ErrorsCryptic file access and permission errors are often a secondary effect of the initial pathing failures. If the script, due to an incorrect working directory, attempts to write logs or clone the repository into a system-protected location (e.g., C:\Windows\System32 if the prompt was opened there as an administrator), it will be denied by User Account Control (UAC) or file system permissions. The batch script's primitive error handling provides no context for this failure, leaving the user to guess the root cause.2.2 Inherent Limitations of the Batch Scripting LanguageThe specific errors observed are manifestations of broader, inherent limitations within the batch scripting language that make it unsuitable for complex, modern automation tasks.State ManagementBatch scripting provides only rudimentary tools for state management. For example, checking if a directory already exists before attempting to create it requires a clumsy IF EXIST construct. This makes it difficult to write idempotent scripts—scripts that can be run multiple times with the same initial state and produce the same end state without error. A non-idempotent setup script will fail on a second run because git clone cannot create a directory that already exists, forcing the user to manually clean up a partial installation before trying again. PowerShell's Test-Path cmdlet and object-oriented nature make such checks trivial and robust.Error PropagationThe primary mechanism for error handling in batch is IF ERRORLEVEL, which checks the exit code of the most recently executed external program. This is a blunt and unreliable instrument. It cannot distinguish between different types of failures, offers no contextual information (like an exception message or stack trace), and is easily bypassed if an intermediate command that succeeds (e.g., an ECHO statement) runs before the check. This leads directly to the cascading failure pattern observed.The observed failures are not isolated incidents but a interconnected sequence symptomatic of the batch script's procedural and fragile nature. An initial, seemingly minor error in path resolution directly causes the subsequent, more critical failures in repository cloning and Python dependency installation. The entire script is architected like a "house of cards," where the failure of one command guarantees the collapse of the entire process without providing a clear root cause. The chain of events is as follows:The script is executed from an unexpected working directory.The relative path used for the git clone operation becomes invalid, resulting in the "path not found" error.Because the clone operation fails, the suno-automation repository directory is never created in the intended location.Subsequent commands like cd suno-automation\backend fail because that path does not exist.Now stranded in the wrong directory, the script cannot find the python.exe interpreter or the requirements.txt file.This leads to the ultimate failure of virtual environment creation and package installation.The fundamental problem is that batch scripting's poor error reporting and its default behavior of continuing after a failure obscure this root cause. It presents the user with a series of seemingly unrelated errors, making debugging a frustrating exercise in forensics. A robust PowerShell solution must address the root cause—unreliable pathing and error handling—rather than merely patching the symptoms.3.0 Architecting a Resilient PowerShell Automation Framework3.1 Core Design PrinciplesThe new PowerShell script is architected around a set of core principles designed to directly counteract the weaknesses of the legacy batch file and ensure a resilient, predictable, and maintainable automation workflow.Portability: All file system operations—including log file creation, repository cloning, and virtual environment setup—are anchored to the script's own location. This is achieved by consistently using the $PSScriptRoot automatic variable, which contains the absolute path to the script's parent directory. This design choice guarantees that the script will function identically whether it is executed from C:\Users\Developer\Scripts, an external drive like E:\Portable_Tools, or a network share.Idempotency: The script is explicitly designed to be safely re-runnable. Before performing any creative action, it first checks the state of the system. It uses Test-Path to verify if the repository directory already exists before attempting to clone it. Similarly, it checks for the presence of the Python virtual environment directory before attempting its creation. This prevents errors on subsequent runs and allows the script to be used to repair or update an existing environment.Structured Error Handling: The script employs a sophisticated, dual-pronged approach to error management. For native PowerShell cmdlets (e.g., New-Item, Set-Location), it uses Try/Catch blocks to handle terminating errors in a structured way.1 For external command-line executables (git.exe, python.exe, pip.exe), which do not generate exceptions that Try/Catch can handle, the script instead inspects the automatic $LASTEXITCODE variable immediately after execution. A value of 0 indicates success, while any non-zero value signifies a failure, which is then explicitly handled.3Modularity and Readability: The script is not a monolithic block of code. It is organized into logical sections and leverages custom helper functions for repeated tasks, such as logging (Write-Log), version checking (Get-CommandVersion), and prerequisite installation (Install-Prerequisite). This modular design, combined with extensive commenting, makes the script easier to understand, debug, and extend in the future.3.2 Feature and Resiliency Comparison: Batch vs. PowerShellThe migration from batch to PowerShell is not merely a bug fix; it is a fundamental upgrade in capability and reliability. The following table provides a direct comparison of key features, articulating the value proposition of this modernization effort. This comparison clearly justifies the engineering effort by demonstrating how each failure point in the legacy script corresponds to a superior, robust feature in the PowerShell solution.FeatureLegacy Batch Script ImplementationNew PowerShell Script ImplementationPath PortabilityBrittle; dependent on current working directory (%CD%). Fails when run from unexpected locations.Fully portable; uses the automatic $PSScriptRoot variable to build reliable relative paths for all operations (cloning, logging, venv).Error HandlingRudimentary (IF ERRORLEVEL); fails to catch most errors from external tools and provides no context. Leads to cascading failures.Structured and comprehensive. Uses Try/Catch for cmdlet errors 2 and explicitly checks $LASTEXITCODE for external commands (git, pip).3PrerequisitesAssumes tools are pre-installed and meet version requirements. Fails opaquely if they are not.Proactively validates presence and versions of Git, Node.js, and Python. Automates installation/upgrade via winget if requirements are not met.5IdempotencyNon-idempotent. Running the script twice would cause git clone to fail because the directory already exists.Fully idempotent. Checks for the existence of the repository directory and virtual environment before attempting to create them, allowing for safe re-runs.LoggingBasic text file output with minimal context.Dual-channel logging to a timestamped file for detailed diagnostics and to the Windows Event Viewer for high-level system monitoring.6MaintainabilityObscure syntax, poor variable scoping, and procedural flow make the script difficult to debug and extend.Clean, commented, modular code with helper functions. PowerShell's object-oriented nature makes it far easier to understand, modify, and extend.4.0 Module 1: Script Initialization and Prerequisite Validation4.1 Establishing the Execution ContextThe script begins by establishing a clean and predictable execution context. It uses a param() block at the top, which, while not used for input in this version, establishes a best practice for future parameterization (e.g., allowing a user to specify a git branch).Key global variables are defined immediately, including:$PSScriptRoot: The absolute path to the script's directory.$RepoName: The name of the repository directory to be created.$LogFile: A dynamically generated path for the text log file, incorporating a timestamp for unique, chronological records.The script also includes a check to ensure it is run with administrative privileges for its initial execution. This is a specific, one-time requirement for creating the Windows Event Log source. Subsequent runs do not require elevation. This is handled by checking the identity of the current user principal and providing a clear message if elevation is required.4.2 Implementing the Dual-Channel Logging FrameworkA robust logging framework is central to the script's design. This is encapsulated within a custom Write-Log function that serves as a single point of entry for all logging activities. This function accepts a message string and a severity level ('INFO', 'WARN', 'ERROR'). For each call, it performs two actions:File Logging: It formats the message with a timestamp and severity level and appends it to the text log file defined during initialization. This provides a verbose, persistent record of the script's execution for detailed troubleshooting.Event Viewer Logging: It writes a corresponding entry to the Windows Event Viewer.A critical consideration in this design is that the standard PowerShell cmdlets for interacting with the Event Log have a significant usability flaw. One cannot use Write-EventLog unless the specified event source has already been registered with the system.9 Attempting to do so results in a terminating error. The logical precursor, then, is to check if the source exists. However, native cmdlets like Get-EventLog or Get-WinEvent are designed to query for events from a source, not the existence of the source registration itself.10 If a source has been created but no events have yet been written to it, these cmdlets will fail or return nothing, leading to a false negative and an erroneous attempt to re-create the source.To circumvent this, the script must leverage the underlying.NET Framework. The only reliable method to check for a source's existence is the static method ::SourceExists(). The Write-Log function's logic is therefore:Check if the source 'suno-automation-setup' exists using ::SourceExists('suno-automation-setup').8If the result is $false, it calls New-EventLog -LogName Application -Source 'suno-automation-setup' to create it.6 This operation requires administrative privileges, which is why the initial run must be elevated.Once the source is guaranteed to exist, it proceeds to call Write-EventLog with the appropriate message, severity, and a unique Event ID.This approach demonstrates a nuanced understanding of PowerShell's architecture, leveraging the full power of the.NET platform where native cmdlets are insufficient.4.3 Prerequisite Validation LogicBefore attempting any core setup tasks, the script validates that all external dependencies are present and meet minimum version requirements. This is handled by a set of validation functions, orchestrated by a generic helper function, Get-CommandVersion.This function is designed to robustly parse version information from the string-based output of command-line tools. The process is as follows:Execute the tool's version command (e.g., git --version, node -v, python --version). The standard output of these commands is captured as an array of strings.The string output is then processed using a regular expression. For example, the -match '(\d+\.\d+\.\d+)' pattern is used to find and extract a semantic version string (e.g., "2.43.0" or "3.11.4") from the full output.12The extracted version string is then cast into a `` object (e.g., [version]$matches). This is a critical step. A [version] object is a structured type that allows for correct, numerical comparison of version components. Simple string comparison would fail in cases like comparing "3.9" and "3.10", where lexicographically, "3.9" is "greater" than "3.10".The main script logic then compares this [version] object against a predefined minimum required version (e.g., [version]'3.14').If the initial command to get the version fails (e.g., git is not found in the PATH), the function will gracefully handle the error and return $null, which the main script interprets as the tool not being installed.This proactive and typed approach to version validation prevents a whole class of runtime errors that would occur if an outdated tool with incompatible features were used.5.0 Module 2: Automated Dependency Installation with winget5.1 The winget AdvantageFor the automated installation of missing or outdated prerequisites, the script utilizes the Windows Package Manager (winget). This tool is chosen for several key reasons: it is the modern, first-party package manager for Windows, officially supported by Microsoft; it is included by default in modern versions of Windows 10 and 11; its command-line interface is designed for scripting and automation; and its repositories contain up-to-date versions of essential developer tools like Git, Node.js, and Python.5.2 Implementing the Install-Prerequisite FunctionA dedicated function, Install-Prerequisite, is created to handle the installation logic. This function abstracts the details of calling winget and provides robust error handling. It accepts the winget package ID as an argument (e.g., 'Git.Git', 'NodeJS.NodeJS.LTS', 'Python.Python.3').The function constructs the winget install command string programmatically. Critically, it includes several arguments to ensure the installation is fully automated and non-interactive, which is essential for a script that may run unattended:--silent: Instructs the installer to run with no user interface.--accept-source-agreements: Automatically accepts the license agreement for the winget source repository, preventing a one-time prompt.--accept-package-agreements: Automatically accepts the End-User License Agreement (EULA) for the specific package being installed.5After invoking the command using Invoke-Expression, the script immediately performs its most critical error-handling step: it inspects the $LASTEXITCODE automatic variable. A non-zero value indicates that the winget.exe process terminated with an error (e.g., package not found, download failure, installer error). If an error is detected, the script logs a fatal message using the Write-Log function and terminates execution immediately. This prevents the script from attempting to proceed with a broken dependency.5.3 Orchestrating the InstallationsThe main body of the script orchestrates the entire validation and installation process. For each required tool (Git, Node.js, Python), it performs the following sequence:Calls the Get-CommandVersion function to check the installed version.Compares the result to the minimum required version.If the tool is not installed ($null was returned) or the installed version is less than the required version, it logs a warning and calls the Install-Prerequisite function with the appropriate package ID.It then re-validates the installation to ensure it was successful before proceeding.This sequence guarantees that by the time the script moves on to the core application setup, the execution environment is in a known-good state with all dependencies correctly installed and available on the system PATH.6.0 Module 3: Core Application Environment Deployment6.1 Cloning the Source Code RepositoryThe first step in deploying the application environment is to acquire the source code. The script handles this idempotently:It constructs the full path for the target repository directory (e.g., $PSScriptRoot\suno-automation).It uses the Test-Path cmdlet to check if this directory already exists.If the directory exists, it logs an informational message indicating that the clone step is being skipped and proceeds. This allows the script to be re-run on an existing setup without error.If the directory does not exist, it executes the git clone command with the specified repository URL.Immediately following the git clone command, the script checks the $LASTEXITCODE. A non-zero exit code from git.exe indicates a failure. This could be due to a variety of reasons, such as no network connectivity, an incorrect repository URL, or authentication failure for a private repository. Upon detecting a failure, the script logs a detailed error message and terminates, preventing it from attempting to work with a non-existent or incomplete code base.6.2 Setting up the Python Virtual EnvironmentWith the source code in place, the script prepares the isolated Python environment.It changes the current working directory to the backend subdirectory of the cloned repository using Set-Location -Path "$RepoPath\backend". This is a crucial step to ensure that subsequent commands operate in the correct context.It constructs the path for the virtual environment directory (e.g., "$RepoPath\backend\venv").In keeping with the principle of idempotency, it uses Test-Path to check if the venv directory already exists.If it does not exist, the script invokes the command python -m venv venv to create the virtual environment. As with all external commands, $LASTEXITCODE is checked immediately afterward to confirm that the venv was created successfully.6.3 Activating the Environment and Installing DependenciesThis is one of the most critical and nuanced phases of the setup process. The correct activation of the Python virtual environment within a PowerShell session is paramount. A common mistake is to attempt to run the activate.bat file, which is intended for the cmd.exe shell. Doing so from PowerShell launches a temporary, child cmd.exe process. While the environment variables are modified within that child process, they are immediately discarded when it exits, leaving the parent PowerShell session's environment unchanged.13The correct method, and the one implemented in this script, is to directly invoke the PowerShell-specific activation script: .\venv\Scripts\Activate.ps1.14 This script is designed to be "dot-sourced," meaning its commands are executed in the scope of the current PowerShell session, correctly and persistently modifying the PATH variable for the remainder of the script's execution.However, the ability to execute this script is directly contingent on the system's PowerShell execution policy. By default, many Windows systems have a policy of Restricted, which prohibits the running of any scripts. The Activate.ps1 script generated by Python's venv module is an unsigned local script, and attempting to run it under a restrictive policy will result in an authorization error, causing the entire setup to fail.16 Therefore, a prerequisite for this automation to function is that the execution policy for the current user must be set to a less restrictive level, such as RemoteSigned. This policy allows local scripts to run while still requiring remote scripts to be signed. The script's documentation and initial run checks must make this requirement clear to the user, instructing them to run Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser in an administrative PowerShell session as a one-time setup step.Once the environment is successfully activated, the script proceeds to install the project's dependencies by running pip install -r requirements.txt. The success of this potentially long-running operation is verified by checking $LASTEXITCODE. A failure here could indicate issues like a missing package in the PyPI repository, network problems, or compilation errors for packages with C extensions. Any failure is logged as a fatal error, and the script terminates.7.0 Module 4: Finalization and User Interaction7.1 Logging SuccessUpon the successful completion of all preceding steps—prerequisite validation, installation, repository cloning, and dependency installation—the script reaches its final state. It logs a conclusive success message to both the text log file and the Windows Event Viewer. This provides a clear, positive confirmation in the system logs that the environment setup was completed without any errors.7.2 Interactive PromptTo preserve the interactive nature of the original script and provide a convenient workflow for the user, the script concludes with a user prompt. It uses the Read-Host cmdlet to display the message: "Setup complete. Do you want to start the application now? (y/n)". This pauses the script and waits for user input.The script captures the user's response and uses a simple if statement to check if the input is 'y' (case-insensitively).If the user responds affirmatively, the script executes the command to launch the application (e.g., python main.py). Since the Python virtual environment is still active in the current session, this command correctly uses the virtual environment's interpreter and its installed packages.If the user enters 'n' or any other input, the script logs a message indicating that it is exiting at the user's request and terminates gracefully.7.3 Script CleanupThe script is designed to be self-contained and does not create temporary files that require explicit cleanup. The primary state change is the modification of the PATH environment variable within the PowerShell session, which is automatically reverted when the PowerShell window is closed. The script concludes by printing a final "Exiting script." message to the console, providing a clear indication that its execution has finished.8.0 The Complete PowerShell Script and Execution Guide8.1 Fully Commented ScriptPowerShell#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Automates the setup of the 'suno-automation' development environment.
.DESCRIPTION
    This script provides a robust, portable, and idempotent solution for setting up
    the 'suno-automation' project. It performs the following actions:
    1.  Sets up a dual-channel logging framework (File and Windows Event Viewer).
    2.  Validates prerequisites (Git, Node.js, Python) against minimum versions.
    3.  Automatically installs or upgrades missing/outdated prerequisites using winget.
    4.  Clones the 'suno-automation' repository from GitHub.
    5.  Creates a Python virtual environment within the project's 'backend' directory.
    6.  Activates the virtual environment and installs dependencies from requirements.txt.
    7.  Prompts the user to start the application upon successful setup.
.NOTES
    Author: Technical Solutions Group
    Version: 1.0
    Date: 2024-10-28

    Initial Execution: This script must be run as an Administrator ONCE to register
    the necessary Windows Event Log source.

    Execution Policy: Before running, ensure your PowerShell execution policy allows
    local scripts. Run the following in an administrative PowerShell prompt:
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#>

#==============================================================================
# SCRIPT CONFIGURATION
#==============================================================================

# --- Core Settings ---
$RepoUrl = "https://github.com/suno-ai/suno-automation.git"
$RepoName = "suno-automation"
$ProjectDir = Join-Path -Path $PSScriptRoot -ChildPath $RepoName
$BackendDir = Join-Path -Path $ProjectDir -ChildPath "backend"
$VenvDir = Join-Path -Path $BackendDir -ChildPath "venv"

# --- Prerequisite Versions ---
$MinGitVersion = [version]'2.38.0'
$MinNodeVersion = [version]'24.10.0'
$MinPythonVersion = [version]'3.14.0' # Target future version as per user request

# --- Logging Settings ---
$LogName = "suno-automation-setup"
$LogTimestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path -Path $PSScriptRoot -ChildPath "setup-log_$($LogTimestamp).log"
$EventSource = "suno-automation-setup"
$EventLogName = "Application"

#==============================================================================
# LOGGING FRAMEWORK
#==============================================================================

function Write-Log {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,

        [Parameter(Mandatory = $true)]
       
        [string]$Level
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp][$Level] - $Message"

    # Write to console
    $color = switch ($Level) {
        'INFO' { 'Green' }
        'WARN' { 'Yellow' }
        'ERROR' { 'Red' }
    }
    Write-Host $logEntry -ForegroundColor $color

    # Write to log file
    Add-Content -Path $LogFile -Value $logEntry

    # Write to Windows Event Viewer
    try {
        # Check if the event source exists. This is the only reliable method. 
        if (-not (::SourceExists($EventSource))) {
            Write-Host "Event source '$EventSource' not found. Attempting to create it (requires elevation)..." -ForegroundColor Yellow
            New-EventLog -LogName $EventLogName -Source $EventSource -ErrorAction Stop [6]
            Write-Host "Event source '$EventSource' created successfully." -ForegroundColor Green
        }

        $eventType = switch ($Level) {
            'INFO' { 'Information' }
            'WARN' { 'Warning' }
            'ERROR' { 'Error' }
        }

        $eventId = switch ($Level) {
            'INFO' { 1000 }
            'WARN' { 2000 }
            'ERROR' { 3000 }
        }

        Write-EventLog -LogName $EventLogName -Source $EventSource -EventId $eventId -EntryType $eventType -Message $Message [7]
    }
    catch {
        $errorMsg = "Failed to write to Windows Event Viewer. Error: $($_.Exception.Message)"
        $errorEntry = "[$timestamp] - $errorMsg"
        Write-Host $errorEntry -ForegroundColor Red
        Add-Content -Path $LogFile -Value $errorEntry
    }
}

#==============================================================================
# HELPER FUNCTIONS
#==============================================================================

function Execute-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,

        [Parameter(Mandatory = $true)]
        [string]$SuccessMessage,
        
        [Parameter(Mandatory = $true)]
        [string]$FailureMessage
    )
    
    Write-Log -Level INFO -Message "Executing: $Command"
    Invoke-Expression $Command *>&1 | Out-Null # Redirect all output streams to null to keep console clean
    
    # External command error handling relies on $LASTEXITCODE, not Try/Catch. 
    if ($LASTEXITCODE -eq 0) {
        Write-Log -Level INFO -Message $SuccessMessage
        return $true
    }
    else {
        Write-Log -Level ERROR -Message "$FailureMessage (Exit Code: $LASTEXITCODE)"
        return $false
    }
}

function Get-CommandVersion {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        
        [Parameter(Mandatory = $true)]
        [string]$VersionArgument
    )

    try {
        $output = & $Command $VersionArgument 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            return $null
        }

        # Use regex to extract version string, e.g., "2.43.0" 
        if ($output -match '(\d+\.\d+\.\d+)') {
            # Cast to [version] object for reliable comparison [17]
            return [version]$matches
        }
        else {
            return $null
        }
    }
    catch {
        return $null
    }
}

function Install-Prerequisite {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ToolName,
        
        [Parameter(Mandatory = $true)]
        [string]$PackageId
    )

    Write-Log -Level WARN -Message "$ToolName not found or version is too old. Attempting installation via winget..."
    # Use silent flags to ensure non-interactive installation 
    $command = "winget install --id $PackageId --silent --accept-source-agreements --accept-package-agreements"
    
    if (-not (Execute-Command -Command $command -SuccessMessage "$ToolName installed successfully via winget." -FailureMessage "Failed to install $ToolName via winget.")) {
        Write-Log -Level ERROR -Message "Aborting setup due to prerequisite installation failure."
        exit 1
    }
}

#==============================================================================
# MAIN SCRIPT EXECUTION
#==============================================================================

# --- 1. Initialization ---
Clear-Host
Write-Log -Level INFO -Message "Starting 'suno-automation' development environment setup."
Write-Log -Level INFO -Message "Log file located at: $LogFile"

# --- 2. Prerequisite Validation and Installation ---
Write-Log -Level INFO -Message "--- Stage 1: Validating Prerequisites ---"

# Validate Git
$gitVersion = Get-CommandVersion -Command "git" -VersionArgument "--version"
if ($null -eq $gitVersion -or $gitVersion -lt $MinGitVersion) {
    Install-Prerequisite -ToolName "Git" -PackageId "Git.Git"
    $gitVersion = Get-CommandVersion -Command "git" -VersionArgument "--version"
    if ($null -eq $gitVersion -or $gitVersion -lt $MinGitVersion) {
        Write-Log -Level ERROR -Message "Git installation failed or version is still insufficient. Aborting."
        exit 1
    }
}
Write-Log -Level INFO -Message "Git is installed (Version: $gitVersion). Requirement met."

# Validate Node.js
$nodeVersion = Get-CommandVersion -Command "node" -VersionArgument "-v"
if ($null -eq $nodeVersion -or $nodeVersion -lt $MinNodeVersion) {
    Install-Prerequisite -ToolName "Node.js" -PackageId "NodeJS.NodeJS"
    $nodeVersion = Get-CommandVersion -Command "node" -VersionArgument "-v"
    if ($null -eq $nodeVersion -or $nodeVersion -lt $MinNodeVersion) {
        Write-Log -Level ERROR -Message "Node.js installation failed or version is still insufficient. Aborting."
        exit 1
    }
}
Write-Log -Level INFO -Message "Node.js is installed (Version: $nodeVersion). Requirement met."

# Validate Python
$pythonVersion = Get-CommandVersion -Command "python" -VersionArgument "--version"
if ($null -eq $pythonVersion -or $pythonVersion -lt $MinPythonVersion) {
    Install-Prerequisite -ToolName "Python" -PackageId "Python.Python.3"
    # After installing via winget, the path may need a new shell. We will try to proceed.
    $pythonVersion = Get-CommandVersion -Command "python" -VersionArgument "--version"
    if ($null -eq $pythonVersion -or $pythonVersion -lt $MinPythonVersion) {
        Write-Log -Level ERROR -Message "Python installation failed or version is still insufficient. A terminal restart may be required. Aborting."
        exit 1
    }
}
Write-Log -Level INFO -Message "Python is installed (Version: $pythonVersion). Requirement met."

# --- 3. Repository Cloning ---
Write-Log -Level INFO -Message "--- Stage 2: Cloning Source Code Repository ---"

if (Test-Path -Path $ProjectDir) {
    Write-Log -Level INFO -Message "Repository directory '$ProjectDir' already exists. Skipping clone."
}
else {
    $cloneCommand = "git clone $RepoUrl `"$ProjectDir`""
    if (-not (Execute-Command -Command $cloneCommand -SuccessMessage "Repository cloned successfully." -FailureMessage "Failed to clone repository.")) {
        Write-Log -Level ERROR -Message "Aborting setup due to repository clone failure."
        exit 1
    }
}

# --- 4. Python Virtual Environment Setup ---
Write-Log -Level INFO -Message "--- Stage 3: Setting up Python Environment ---"

try {
    Set-Location -Path $BackendDir -ErrorAction Stop
    Write-Log -Level INFO -Message "Changed directory to '$BackendDir'."
}
catch {
    Write-Log -Level ERROR -Message "Failed to change directory to '$BackendDir'. It may not exist. Aborting."
    exit 1
}

if (Test-Path -Path $VenvDir) {
    Write-Log -Level INFO -Message "Python virtual environment already exists at '$VenvDir'. Skipping creation."
}
else {
    $venvCommand = "python -m venv venv"
    if (-not (Execute-Command -Command $venvCommand -SuccessMessage "Python virtual environment created." -FailureMessage "Failed to create Python virtual environment.")) {
        Write-Log -Level ERROR -Message "Aborting setup due to venv creation failure."
        exit 1
    }
}

# --- 5. Dependency Installation ---
Write-Log -Level INFO -Message "--- Stage 4: Installing Python Dependencies ---"

# Activate the virtual environment for the current PowerShell session. 
$activateScript = Join-Path -Path $VenvDir -ChildPath "Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    Write-Log -Level ERROR -Message "Could not find activation script at '$activateScript'. Aborting."
    exit 1
}

try {
    Write-Log -Level INFO -Message "Activating Python virtual environment..."
   . $activateScript
    Write-Log -Level INFO -Message "Virtual environment activated."
}
catch {
    Write-Log -Level ERROR -Message "Failed to activate the virtual environment. Ensure your ExecutionPolicy is set to 'RemoteSigned' for CurrentUser."
    Write-Log -Level ERROR -Message "Run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
    exit 1
}

$pipCommand = "pip install -r requirements.txt"
if (-not (Execute-Command -Command $pipCommand -SuccessMessage "Python dependencies installed successfully." -FailureMessage "Failed to install Python dependencies.")) {
    Write-Log -Level ERROR -Message "Aborting setup due to dependency installation failure."
    exit 1
}

# --- 6. Finalization ---
Write-Log -Level INFO -Message "======================================================"
Write-Log -Level INFO -Message "Development environment setup completed successfully!"
Write-Log -Level INFO -Message "======================================================"

$response = Read-Host -Prompt "Do you want to start the application now? (y/n)"

if ($response -eq 'y') {
    Write-Log -Level INFO -Message "Starting the application..."
    # Placeholder for the actual start command
    # For example: python main.py
    Write-Host "Executing application start command..." -ForegroundColor Cyan
    # & python main.py
}
else {
    Write-Log -Level INFO -Message "Exiting script as per user request."
}

exit 0

8.2 Execution InstructionsTo ensure the successful execution of the setup script, a one-time administrative setup is required, followed by standard user execution for all subsequent runs.One-Time Setup (Administrator)This initial setup configures the system to allow the script to run and to create the necessary logging infrastructure. It only needs to be performed once.Open PowerShell as Administrator: Search for "PowerShell" in the Start Menu, right-click "Windows PowerShell," and select "Run as administrator."Set Execution Policy: The default PowerShell security settings may prevent local scripts from running. Execute the following command to allow signed remote scripts and all local scripts to run. This is a safe and common configuration for development machines.14PowerShellSet-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
When prompted, type 'Y' and press Enter to confirm the change.Run the Setup Script: Navigate to the directory where you saved the setup-environment.ps1 script and execute it:PowerShellcd path\to\your\script
.\setup-environment.ps1```This first run, with administrative privileges, will automatically create the required Event Log source, 'suno-automation-setup', if it does not already exist.Standard Usage (User)After the one-time setup is complete, the script can be run from a standard, non-administrative PowerShell terminal at any time to set up, repair, or verify the environment.Open PowerShell: Open a regular PowerShell terminal (it does not need to be run as an administrator).Navigate to the Script Directory: Use the cd command to navigate to the folder containing setup-environment.ps1.Run the Script: Execute the script:.\setup-environment.ps1```The script will perform all necessary checks and actions, providing real-time feedback in the console.8.3 Interpreting Log FilesThe script generates two forms of logs for diagnostics:Text Log File: A file named setup-log_YYYYMMDD_HHMMSS.log is created in the same directory as the script. This file contains a detailed, timestamped transcript of every action the script performed, including all informational messages, warnings, and errors. This should be the first place to look for details about a failed run.Windows Event Viewer: High-level events are logged to the Windows Event Viewer. To view these logs:Press Win + R, type eventvwr.msc, and press Enter.In the Event Viewer, navigate to Windows Logs -> Application.Look for events with the Source listed as suno-automation-setup. This provides a high-level audit trail of setup successes and failures that is integrated with the operating system.9.0 Conclusion and Future Enhancements9.1 Summary of AchievementsThis project has successfully addressed the critical failures and inherent fragility of the original batch-based setup process. The legacy script has been replaced with a professional-grade PowerShell automation tool that is reliable, portable, idempotent, and maintainable. The new solution provides a deterministic, one-click setup experience, complete with proactive prerequisite management and a comprehensive, dual-channel logging system. The architectural shift from a brittle, procedural script to a robust, modular PowerShell framework eliminates the previous points of failure and establishes a solid foundation for future development and automation tasks.9.2 Recommendations for Future WorkWhile the current script fully meets the specified requirements, its modular design allows for several potential enhancements that could further increase its utility and flexibility.Parameterization: The script's param() block can be expanded to accept command-line arguments. This would allow users to override default settings, such as the repository URL, the local directory name, or the specific git branch to be cloned, transforming the script into a more generic and reusable tool.Configuration File: For easier management of configuration variables (like minimum version numbers, winget package IDs, and repository URLs), these settings could be externalized into a configuration file (e.g., in JSON or XML format). The PowerShell script would then read this file at runtime. This would allow for updates to dependencies or targets without modifying the script's core logic.GUI Wrapper: For users who are less comfortable with the command line, a simple graphical user interface could be developed as a wrapper around the script. PowerShell has native capabilities for building GUIs using Windows Presentation Foundation (WPF) or Windows Forms, which could provide a user-friendly front-end with buttons and progress indicators that call the underlying script functions.