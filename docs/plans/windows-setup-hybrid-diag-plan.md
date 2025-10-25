# Plan: Hybrid Logging Diagnostics for `setup-windows.bat`

**Objective:** To diagnose the script failure by implementing a hybrid logging strategy. This approach will keep the console clean by displaying only high-level status updates, while capturing all raw command output and detailed trace information in the log file.

---

## 1. Implement a `DEBUG` Log Level

The `:log` function will be updated to support a `DEBUG` log level. Messages logged at this level will be written **only** to the log file, not to the console. This is ideal for verbose tracing.

**File:** `scripts/windows/setup-windows.bat`

#### Proposed Change to `:log` function:

```batch
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

REM Output to console (exclude DEBUG level)
if /i not "%strLogLevel%"=="DEBUG" (
    echo [%strLogLevel%] !strLogMessage!
)

REM Output to log file (all levels)
echo !strFormattedTime! [%strLogLevel%] !strLogMessage! >> "%strLogFile%"

REM Output to Event Viewer
eventcreate /ID 1 /L APPLICATION /T %strEventType% /SO "%strEventSource%" /D "!strLogMessage!" >nul 2>&1

goto :eof
```

## 2. Redirect All Raw Command Output to Log File

Every external command (`git`, `winget`, `node`, `npm`, `python`, `pip`, etc.) will have its standard output and standard error redirected to the log file. The structured logs from the `:log` function will continue to appear on the console as before.

**File:** `scripts/windows/setup-windows.bat`

#### Example Change:
**Current Code (Line 71):**
```batch
winget --version
```
**Proposed Change:**
```batch
winget --version >> "%strLogFile%" 2>&1
```
*This `>> "%strLogFile%" 2>&1` redirection will be applied to **every** external command call throughout the script.*

## 3. Add `DEBUG` Trace Markers

To trace the execution flow, `DEBUG` log calls will be added at the beginning and end of every function.

**File:** `scripts/windows/setup-windows.bat`

#### Example Instrumentation for `:ensureGit`:
```batch
:ensureGit
call :log "DEBUG" "Entering :ensureGit"
call :log "INFO" "Checking Git installation..."
git --version >> "%strLogFile%" 2>&1
if errorlevel 1 (
    ...
) else (
    call :log "SUCCESS" "Git is already installed."
)
call :log "DEBUG" "Exiting :ensureGit"
goto :eof
```
*This pattern will be applied to all subroutines.*

## 4. Improve the Final Status Report

The final status display will be enhanced to provide a clear, default error message if the `strInstallReport` variable is empty, preventing the "ECHO is off" issue.

**File:** `scripts/windows/setup-windows.bat`

#### Proposed Change in `:displayFinalStatus`:
```batch
...
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
...
```

---

**Next Steps:**
Once you approve this plan, I will request to switch to **Code mode** to apply these changes. The resulting log file will contain the raw output needed for a definitive diagnosis, while the console remains readable.