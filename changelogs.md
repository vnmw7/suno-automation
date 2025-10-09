# Changelogs

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Manual Login Timeout Issue** (2025-10-09)
  - Fixed manual login timeout when saved session already exists
  - Location: `backend/lib/login.py` - `manual_login_suno()` function (lines 499-513)
  - Issue: Manual login would timeout after 10 seconds if user had a saved session, because the page never reached "networkidle" state
  - Solution:
    - Wrapped `wait_for_load_state("networkidle")` in try-catch to gracefully handle timeout
    - Added early login detection using `is_truly_logged_in_suno()` helper function immediately after page load
    - Now immediately detects existing sessions and returns success instead of waiting for timeout
  - Impact: Users with saved sessions will no longer see false "Manual login failed or was cancelled" alerts
