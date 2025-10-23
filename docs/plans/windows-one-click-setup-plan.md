"""
System: Suno Automation
Module: Windows Setup Automation
File URL: docs/plans/windows-one-click-setup-plan.md
Purpose: Outline the implementation steps for a one-click Windows bootstrap script that provisions all project prerequisites.
"""

# Windows One-Click Bootstrap Plan

## Requested Outcome
- Deliver a Windows batch script that an end-user can double-click to install Git, Node.js (≥20), and Python 3.11 via Winget when needed.
- Automatically clone or update the `suno-automation` repository, set up the backend virtual environment, install Python dependencies (including Camoufox) and download the Camoufox browser payload.
- Install frontend Node dependencies, scaffold the required `.env` files from their `.example` templates, and prompt the user for essential secrets.
- Leave the workspace ready to launch via the existing `start.bat` script, with clear success messaging and guidance on any manual follow-up.

## Planned File Changes

1. `setup-windows.bat` (new file at the repository root)  
   - Purpose: encapsulate the end-to-end provisioning flow described above.  
   - Current snippet: _File does not yet exist._

2. `readme.md` (update `## Getting Started`)  
   - Purpose: advertise the new one-click setup path and clarify modern prerequisite versions.  
   - Current snippet:
     ```markdown
     ### Prerequisites
     - Python 3.10+
     - Node.js 18+
     - PostgreSQL database

     ### Installation
     1. Clone the repository:
        ```bash
        git clone https://github.com/your-username/suno-automation.git
        cd suno-automation
        ```
     ```

## Implementation Steps

1. **Bootstrap Structure inside `setup-windows.bat`**  
   - Add header metadata per project standard (`REM System`, `REM Module`, etc.).  
   - Enable delayed expansion (`SetLocal EnableExtensions EnableDelayedExpansion`) and group task-specific helpers into dedicated labels (e.g., `:ensureWinget`, `:ensureGit`).  
   - Define strongly-typed variable names with mandated prefixes (e.g., `set strRepoUrl=...`, `set blnNeedsInstall=0`).

2. **Pre-flight Safety Checks**  
   - Detect administrative rights; prompt the user to relaunch with elevation when Winget installs are required.  
   - Validate that `winget` is available; otherwise, surface actionable instructions and gracefully exit using the Result pattern (`blnSuccess` flag plus status message).  
   - Confirm network access before attempting downloads.

3. **Ensure Core Toolchain**  
- For each dependency (Git.Git, OpenJS.NodeJS.LTS, Python.Python.3.11):  
    - Always invoke `winget install --exact --accept-package-agreements --accept-source-agreements <Id>` to guarantee the expected version is present, upgrading in place when already installed.  
    - Collect failures into a shared report string to show at the end if installations fail.

4. **Fetch or Refresh Repository Content**  
- Determine the working directory (`set strScriptRoot=%~dp0`).  
- If `.git` directory exists, run `git fetch --all --prune` then `git pull` to ensure up-to-date code.  
- If `.git` is absent, clone `https://github.com/vnmw7/suno-automation.git` into `%USERPROFILE%\suno-automation`, then re-launch the script from the freshly cloned root to continue provisioning.

5. **Backend Environment Setup**  
   - Navigate to `backend`, create `.venv` if missing (`python -m venv .venv`), and activate via `call .venv\Scripts\activate`.  
   - Upgrade `pip`, install `pip install --upgrade pip` followed by `pip install -r requirements.txt`.  
   - Execute `camoufox fetch` to download the patched Firefox profile.  
   - Deactivate the virtual environment (`call deactivate`) or close the subshell to avoid pollution.

6. **Frontend Dependency Installation**  
   - Run `npm install` within `frontend` (guard with `npm config set fund false` to keep output tidy).  
   - Offer `npm run build` as an optional post-step, skipping by default to respect the Minimum Viable Approach.

7. **Environment File Provisioning**  
- Copy `.env.example` to `.env` for backend, frontend, and root when missing.  
- Overwrite each `.env` with the sanctioned defaults bundled directly in the batch file.  
  - Root `.env`: `TAG=latest`, `CAMOUFOX_SOURCE=auto`.  
  - Backend `.env`: replicate the contents of `backend/.env` (Supabase credentials, database connection parameters, Google AI key).  
  - Frontend `.env`: replicate the contents of `frontend/.env`, ensuring the Supabase credentials and `VITE_API_URL=http://localhost:8000` are identical.  
- Emit a reminder that secrets can be edited later if refreshed.

8. **Final Status & Next Actions**  
   - Surface consolidated success/failure summary, including pending manual tasks (e.g., “Update Supabase secrets in backend/.env”).  
   - Offer to launch `start.bat` automatically; default to “no” to avoid surprise container spins.  
   - Exit with non-zero code whenever any mandatory stage fails so CI or end-user wrappers can detect issues.

9. **Documentation Update (`readme.md`)**  
- Reconcile prerequisite versions with the new automation (Python 3.11, Node.js LTS ≥20).  
- Introduce a “One-Click Windows Setup” subsection pointing to `setup-windows.bat`, clarifying that the script requires Windows 10+ with Winget and administrator privileges.  
   - Retain manual setup steps as the fallback path.

## Testing Strategy
- Execute the script on a fresh Windows test VM without Git/Node/Python to verify Winget installations succeed.  
- Re-run on a machine where dependencies already exist to confirm the version checks skip reinstallation gracefully.  
- Validate backend camoufox provisioning by confirming `%USERPROFILE%\.camoufox` or backend cache receives the downloaded assets.  
- Smoke test by running `start.bat` after the script finishes and ensuring both services start without missing dependency errors.

## Open Questions for Stakeholder
- None. Instructions updated per stakeholder guidance.
