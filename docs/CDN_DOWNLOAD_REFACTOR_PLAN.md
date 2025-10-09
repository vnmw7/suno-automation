# Plan: Refactor CDN Download Logic for Authenticated Sessions

**Objective:** Resolve the consistent HTTP 403 Forbidden errors during CDN downloads by implementing a hybrid authentication and download architecture. This plan will use browser automation to acquire authentication cookies and a lightweight HTTP client to perform the actual downloads.

---

## 1. Context and Problem Analysis

- **Problem:** The `downloadSongsFromCdn` function in `backend/api/orchestrator/utils.py` fails with HTTP 403 Forbidden because it makes direct, unauthenticated requests to Suno's CDN.
- **Root Cause:** Suno's CDN requires authentication, likely via session cookies, to grant access to generated media. The current `aiohttp` requests lack this authentication context.
- **Evidence:** The Playwright-based fallback (`download_song_v2.py`) succeeds because it operates within an authenticated browser session, implicitly providing the necessary cookies.
- **Goal:** Refactor the primary download mechanism to use an authenticated `aiohttp` session, making the CDN-first approach viable and efficient, while retaining the Playwright method as a true fallback.

---

## 2. Architectural Plan: Hybrid Authentication Model

This plan adopts a hybrid model that separates the concerns of authentication and data transfer.

1.  **Authentication Agent (Playwright/Camoufox):** Its primary role is to perform the initial login and establish an authenticated session. It will then be used to extract the session cookies.
2.  **High-Performance Transporter (aiohttp):** Its role is to perform the actual file downloads efficiently, using the authentication state (cookies) provided by the Authentication Agent.

---

## 3. Task Breakdown and Implementation Steps

### **Phase 1: Cookie Management Utilities**

**Goal:** Create a centralized, robust mechanism for extracting, storing, and retrieving authentication cookies from the browser session.

**Task 1.1: Create a New Cookie Utility Module**
-   **Action:** Create a new file: `backend/utils/session_utils.py`.
-   **Purpose:** This module will encapsulate all logic related to browser session and cookie management, decoupling it from the login and download logic.

**Task 1.2: Implement Cookie Extraction Function**
-   **File:** `backend/utils/session_utils.py`
-   **Action:** Create an `async` function `get_session_cookies(context) -> list`.
    -   This function will take a Playwright `BrowserContext` object as input.
    -   It will call `context.cookies()` to extract all cookies for the `suno.ai` domain.
    -   It will return a list of cookie dictionaries.
-   **Rationale:** Centralizes the cookie extraction logic.

**Task 1.3: Implement Cookie Persistence**
-   **File:** `backend/utils/session_utils.py`
-   **Action:**
    -   Create a function `save_cookies_to_file(cookies, path)`.
    -   Create a function `load_cookies_from_file(path)`.
    -   These functions will handle saving the extracted cookies to a JSON file (e.g., `backend/camoufox_session_data/cookies.json`) and loading them back.
-   **Rationale:** Allows the system to reuse authentication sessions across multiple runs, minimizing the need for frequent, slow logins.

### **Phase 2: Integrate Cookie Extraction into Login Flow**

**Goal:** Modify the existing login process to save the authentication cookies upon a successful login.

**Task 2.1: Update Manual Login**
-   **File:** `backend/lib/login.py`
-   **Action:** In the `manual_login_suno` function, after a successful login is detected, call the new utility functions.
    -   Get the browser context from the `page` object (`page.context`).
    -   Call `get_session_cookies(context)`.
    -   Call `save_cookies_to_file()` to persist the extracted cookies.
-   **Rationale:** Ensures that a successful manual login populates the cookie cache for subsequent automated runs.

### **Phase 3: Refactor the CDN Download Function**

**Goal:** Re-architect `downloadSongsFromCdn` to use the persisted authentication cookies.

**Task 3.1: Modify `downloadSongsFromCdn` Signature and Logic**
-   **File:** `backend/api/orchestrator/utils.py`
-   **Action:**
    1.  At the beginning of the function, call `session_utils.load_cookies_from_file()` to get the saved cookies.
    2.  If no cookies are found, return an error indicating that authentication is missing.
    3.  Create an `aiohttp.CookieJar`.
    4.  Iterate through the loaded cookies and add them to the `CookieJar`. Pay attention to the `domain` and `path` attributes of each cookie.
    5.  Instantiate the `aiohttp.ClientSession` with the populated `cookie_jar`.
    6.  The rest of the function (making the GET request, streaming the file) remains largely the same, but will now be executed with an authenticated session.

**Task 3.2: Implement Intelligent Error Handling**
-   **File:** `backend/api/orchestrator/utils.py`
-   **Action:** In the `except` block of `downloadSongsFromCdn`, specifically check for the HTTP 403 status.
    -   If a 403 error occurs, it strongly implies the cached cookies are stale or invalid.
    -   The function should return a specific error type (e.g., a dictionary with `"error": "authentication_failed"`) to signal to the caller that a re-authentication is required.
-   **Rationale:** This creates a self-healing mechanism. A 403 error is no longer a generic failure but a specific signal to refresh the session.

### **Phase 4: Update the Orchestrator Logic**

**Goal:** Adapt the main workflow to handle the new authentication-aware download logic.

**Task 4.1: Refactor `download_both_songs`**
-   **File:** `backend/api/orchestrator/utils.py`
-   **Action:**
    1.  Modify the loop that calls `downloadSongsFromCdn`.
    2.  Check the return value. If the error indicates `"authentication_failed"` (from Task 3.2), the system should:
        a. Log the authentication failure.
        b. **(Future Enhancement)** Trigger a re-login flow automatically. For this initial implementation, we will rely on the Playwright fallback.
    3.  The existing logic to fall back to `download_song_v2` (Playwright) when CDN fails will now correctly handle authentication failures as one of the triggers.

---

## 4. Validation Plan

1.  **Clear Cache:** Manually delete any existing `backend/camoufox_session_data/cookies.json` file.
2.  **Manual Login Test:** Run the application. It should prompt for a manual login. Complete the login. Verify that `cookies.json` is created and contains valid-looking cookie data.
3.  **CDN Download Test:** Run the song generation workflow again.
    -   **Expected:** The `downloadSongsFromCdn` function should now successfully download the MP3 files on the first attempt without any 403 errors.
    -   **Verify:** Check the logs to confirm that `aiohttp` is being used and that there is no fallback to Playwright for the download.
4.  **Stale Cookie Test:** Manually edit `cookies.json` to invalidate the session cookie value.
    -   **Expected:** The `downloadSongsFromCdn` function should fail with a 403 error, and the orchestrator should correctly fall back to the Playwright-based `download_song_v2`.

---

## 5. Risk and Confidence

-   **Confidence:** High. This architectural pattern is a standard and robust solution for interacting with web services that rely on cookie-based authentication.
-   **Risk:** Suno.ai could change its authentication mechanism (e.g., introduce CSRF tokens, switch to JWT in headers).
-   **Mitigation:** The proposed modular design (`session_utils.py`, `login.py`) isolates the authentication logic, making it easier to adapt to future changes without altering the entire download workflow.
