"""
System: Universal Investigation & Implementation Rules
Module: General Rules
Purpose: Provide a universal, project-agnostic set of rules and templates to follow when creating implementation plans or investigating bugs. Designed to be copy-pasted into any repository's rulebook or used by automated tools and external AIs.
"""

# Universal Investigation & Implementation Guidelines

Use this file as the authoritative template whenever you prepare an implementation plan or investigate a bug in any software project. These rules are intentionally generic so they can be applied to diverse stacks (Python, Node, Java, Go, etc.), architectures (monolith, microservices), and repositories.

Summary: for any planned change or investigation, identify scope, list every possibly-relevant file with exact repo-relative paths, include a concise architecture visualization of only the relevant areas, embed the exact file contents, and produce a clear, minimally-invasive implementation or remediation plan.

---

## Required outputs for every plan/investigation

Every delivered plan or investigation document MUST include the following sections:

1. Metadata
   - Title
   - Author (person or tool)
   - Date/time (UTC)
   - Brief one-line summary
2. Reproduction or Acceptance Criteria
   - Steps to reproduce a bug (commands, inputs, environment) or feature acceptance criteria.
3. Scope & Impact
   - What will change / what might be affected
4. Files inspected (exact repo-relative paths) — REQUIRED
   - For each file: path and short reason it's relevant.
5. Full file contents for every inspected file — REQUIRED
   - Paste exact file contents beneath the file header (so external tools/AIs can reason from exact code).
6. Focused architecture/structure visualization (ASCII) — REQUIRED
   - Include only files and modules relevant to this investigation (annotate each entry with one short reason).
7. Root cause analysis (for bugs) or design description (for features)
8. Proposed minimal fix or implementation plan
   - Smallest change to resolve the issue or implement the feature.
9. Tests to add or modify
   - Include specific test names or code snippets for unit/integration tests that reproduce the bug and validate the fix.
10. Edge cases and non-functional considerations
   - Performance, security, backward compatibility, migrations, concurrency.
11. Run & verification steps
   - Exact commands to run locally (shell/PowerShell) and expected outputs.
12. Rollout and rollback plan
13. Status and next steps

---

## How to identify possibly-relevant files (universal heuristics)

Start from the failing symptom or new feature requirement and expand using these steps. Include any file that matches one of these heuristics.

1. Entry points and routing
   - Backend: application entry (e.g., `main.py`, `app.js`, `server.go`, `index.js`) and route definitions.
   - Frontend: `package.json`, main app entry, and UI components that call the API.
2. Imports and dependencies
   - Files imported directly by the entry point or by previously identified files (trace one level at a time until you reach libraries).
3. Configuration and environment
   - `*.env` examples, `pyproject.toml`, `package.json`, `requirements.txt`, `Dockerfile`, `k8s/` manifests, CI configs like `.github/workflows`.
4. Data layer
   - DB schema, migration files, ORM models, raw SQL files, and files that perform queries.
5. Business logic and libraries
   - Modules under `lib/`, `utils/`, `services/`, domain folders with core logic.
6. Tests
   - Unit/integration tests related to the component or failing behavior.
7. Build and packaging
   - Build scripts, bundlers, Dockerfiles, packaging manifests.
8. Observability
   - Logging configuration, telemetry, alert rules, and any scripts that collect or parse logs.

Heuristic rules:
- Use static analysis to follow imports; include any directly imported module up to the repository boundary.
- Include config and environment files even if they are not code (they change runtime behavior).
- If API requests are involved, include both client and server sides.

---

## How to present included file contents

For every file you list in the "Files inspected" section, include a header and a fenced code block with the exact file contents. Use the repository-relative path as the header.

Example:

### File: `backend/main.py`
```python
<exact file contents>
```

Do not paraphrase or remove code — include exact contents. If a file is missing or intentionally empty, include a short note and the path.

---

## Focused architecture visualization (template)

Create a trimmed ASCII tree containing only relevant files and folders. Limit to ~25 lines. Each node must be annotated with a 1-line reason.

Example:

Project root
├─ backend/
│  ├─ main.py                # entrypoint — registers routes
│  ├─ services/songs.py      # business logic for songs
│  └─ lib/supabase.py        # DB helper used by songs
├─ frontend/
│  ├─ package.json           # scripts & dependencies
│  └─ app/songs/client.tsx   # UI component calling backend
├─ migrations/               # DB migrations relevant to song table
└─ tests/                    # failing integration test: tests/test_songs.py

Only include files you actually inspected for this investigation.

---

## Minimal change philosophy

Always prefer the smallest change that fully resolves the issue. Avoid adding large refactors or extra features as part of a bug fix. Document tradeoffs and add follow-up tasks if additional cleanup is desired.

---

## Template: Implementation Plan (short form)

- Title:
- Author:
- Date:
- Summary:
- Scope (what's in/out):
- Files to change (paths, and paste current contents for each):
- Design (data flow & key changes):
- Tasks:
  1. Change file A: lines X-Y (describe change)
  2. Add file B
  3. Add tests
  4. Update docs
- Verification steps (how to run and expected results):
- Rollout & migration steps:
- Rollback plan:
- Risks & mitigations:

---

## Template: Investigation Report (short form)

- Title:
- Author:
- Date:
- One-line symptom summary:
- Reproduction steps (exact commands, env vars):
- Files inspected (list of repo-relative paths):

---

(Then paste each file's contents under a header as described in §3 above.)

- Root cause analysis:
- Proposed minimal fix:
- Tests added/modified:
- Steps to verify fix and confirm no regressions:
- Status and next steps:

---

## Edge cases & universal checks to include

- Missing files, empty config values.
- Environment variations (OS path separators, env vars, timezone/locale differences).
- Dependency version mismatches and lockfile drift.
- Auth and permission errors.
- Database migrations and existing data compatibility.
- Concurrency or async race conditions.
- Backward compatibility with public APIs.

---

## Recommended quick commands (cross-platform hints)

Use exact commands for the environment you expect. Examples shown below for PowerShell and POSIX shells.

PowerShell (Windows):

```powershell
# Run tests (Python)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q

# Run Node frontend
cd frontend
npm install
npm run dev
```

POSIX (Bash / macOS / Linux):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q

cd frontend
npm install
npm run dev
```

For containerized projects, include `docker build` and `docker run` examples.

---

## Required metadata and automation notes

- Always include the list of file paths and full contents to make the document machine-readable.
- If an automated assistant generates the plan, it must include a `files_inspected` JSON array at the end of the document listing all file paths and checksums (sha256) for traceability.
- If files are too large, include the first and last 200 lines and note truncation explicitly — but prefer full contents whenever possible.

---

End of universal guideline.
