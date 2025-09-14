# Product Requirements Document (PRD)

Automated AI Song Generator for Bible Passages (Suno Automation)

## 1. Summary

Build an end-to-end system that automates creating, downloading, reviewing, and curating AI-generated songs on the Suno website using Bible passages. The system consists of:

- Python backend (FastAPI) that orchestrates: AI-assisted verse range and song-structure generation, Suno browser automation for song creation and download, AI quality review of audio, file management, and an orchestrated multi-attempt workflow.
- Frontend (Remix + Tailwind) for GUI-driven flows and a final manual review step.
- Supabase for persisting song-structure planning data and derived metadata.

Key Constraint: The last step remains manual review by a human before distribution/use.


## 2. Goals and Non-Goals

Goals
- Automate most of the song creation lifecycle for given Bible book/chapter/verse ranges and style/title inputs.
- Provide a reliable workflow that produces two song variants per attempt and retries up to a policy-defined number of attempts when quality is low.
- AI-assisted review to reduce human burden; final manual review in a single, simple UI.
- Store planning artifacts (verse ranges, song structures, tone, styles) for reuse and auditability.
- Provide a clear, documented API for the frontend and for potential CLI/batch automation.

Non-Goals
- No direct distribution/publishing pipeline in v1 (beyond file download and final review folders).
- No complex user/auth management; local usage with basic login into Suno via automated browser.
- No custom model training; uses external models (Gemini) and Suno’s website.
- UI/UX polish is secondary to core functionality for this internal tool.


## 3. Stakeholders & Personas

- Content Operator / Reviewer (Primary): Sets parameters (Book, Chapter, Verse Range, Style, Title), kicks off workflows, and performs the final manual review.
- Engineer/Maintainer: Monitors reliability, handles updates when Suno/website flows change, manages configs/quotas.


## 4. User Stories

- As a Content Operator, I can log into Suno via Google or Microsoft so the system can automate song generation on my account.
- As a Content Operator, I can generate verse ranges and song structures for a target Bible passage to guide song creation.
- As a Content Operator, I can initiate an orchestrated workflow that generates two songs, downloads them, runs AI reviews, and retries if needed.
- As a Reviewer, I can load the list of candidate songs for a specific Bible passage and listen, annotate, and mark final decisions.
- As an Engineer, I can debug download and review steps separately using dedicated debug endpoints.


## 5. In Scope vs Out of Scope

In Scope
- Automated Suno login flows (Google and Microsoft).
- Verse-range generation and song-structure generation via Gemini.
- Suno automation to create two songs per generation request.
- Downloading the latest generated songs and organizing files into lifecycle folders (e.g., pending_review, final_review).
- AI review using Gemini with rate-limit awareness and backoff.
- Orchestrated 3-attempt workflow with re-roll logic and fallback.
- Manual review UI to audition and finalize.

Out of Scope (v1)
- Multi-user roles, access control and audit logs.
- External publishing, cataloging, or licensing workflows.
- Cloud scaling/queue workers beyond local sequential execution.


## 6. Functional Requirements

### 6.1 Authentication to Suno (Browser Automation)
- Support initiating Suno login via Google: `GET /login`. Backend calls `utils.suno_functions.login_suno()`.
- Support initiating Suno login via Microsoft: `GET /login/microsoft`. Backend calls `lib.login.login_google()` then `lib.login.suno_login_microsoft()`.
- Frontend shows a simple “Start/Login” page and routes to main UI on success.

Acceptance Criteria
- Hitting `http://127.0.0.1:8000/login` triggers the login automation and returns `{ "success": true|false }`.
- Hitting `http://127.0.0.1:8000/login/microsoft` logs in via the Microsoft path.
- On success, frontend navigates to `/main`.

### 6.2 AI-Assisted Planning (Verse Ranges & Song Structure)
- Generate verse ranges for a book chapter using Gemini, store each range into Supabase `song_structure_tbl`:
	- `POST /ai-generation/verse-ranges` with `{ book_name, book_chapter }`.
	- `GET /ai-generation/verse-ranges?book_name=...&book_chapter=...` returns existing or generates if missing.
- Generate song structure for a given passage:
	- `POST /ai-generation/song-structure` with `{ strBookName, intBookChapter, strVerseRange, structureId? }`.
	- Persist structure JSON, tone (0|1), and styles[] in `song_structure_tbl`.
- Style selection uses chapter and tone via `utils.assign_styles.get_style_by_chapter`.

Acceptance Criteria
- A request for verse ranges yields a comma-separated list parsed to an array and inserts rows in Supabase.
- A song-structure request produces a valid JSON dictionary (keys like verse1/chorus/bridge etc.), stores JSON, `tone`, and `styles` in Supabase.
- Repeated calls return existing structure unless regeneration is requested (via `structureId`, behavior can be extended later).

### 6.3 Song Generation (Suno Website)
- `POST /song/generate` accepts `{ strBookName, intBookChapter, strVerseRange, strStyle, strTitle }` and triggers website automation to generate two songs.
- Each generation attempt produces two variants. Orchestrator may call this step multiple times.

Acceptance Criteria
- Endpoint returns `{ success, message, result }` with logs on the server. Errors return `{ success: false, message, error }`.

### 6.4 Downloading Songs
- `POST /song/download/` downloads a song to a configured path (default `backend/songs/pending_review`).
	- Request supports either `{ song_id }` or `{ strTitle, intIndex }` (negative index for newest: -1, -2).
	- Validates `download_path` and creates directories if needed.
- File naming: downstream functions should produce consistent, parseable names and return the full file path.

Acceptance Criteria
- Successful response: `{ success: true, file_path, song_title, song_index }`.
- Failure response: `{ success: false, error, song_title, song_index }` with HTTP 4xx for bad input.
- Frontend uses the newer `downloadSongAPI` targeting `/song/download/` (deprecate older `/download-song`).

### 6.5 AI Review of Audio
- `POST /ai_review/review/` accepts `{ audio_file_path, pg1_id }` and returns a verdict: `continue` or `re-roll` (or `error`).
- Applies rate limits from `backend/config/ai_review_config.py` (default Flash model, sequential processing) and includes intentional delays between API calls.
- May delete files or move files based on verdict; provides messages in response.

Acceptance Criteria
- Review returns `{ success, verdict, first_response?, second_response?, audio_file?, deletion_message?, move_message? }`.
- Validation ensures file exists and required fields present; useful HTTP 4xx/5xx on errors.

### 6.6 Orchestrated Workflow
- `POST /orchestrator/workflow` coordinates a full attempt:
	1) Generate two songs on Suno for given inputs.
	2) Wait for processing (time baked into automation logic).
	3) Download both songs (use negative indexing -1 and -2).
	4) AI review each song.
	5) If both fail or verdict is `re-roll`, re-generate up to 3 attempts.
	6) On success or after final attempt, ensure outputs are moved to `songs/final_review`.
- Debug endpoints:
	- `POST /orchestrator/debug/download` to test downloads.
	- `POST /orchestrator/debug/review` to test review logic.

Acceptance Criteria
- Response provides `{ success, message, total_attempts, final_songs_count, good_songs?, re_rolled_songs?, workflow_details? }`.
- The orchestrator must never end with zero artifacts: after final attempt, move last outputs to `final_review` even if AI verdicts were negative.

### 6.7 Streaming & Manual Review
- Stream audio from backend in a sandboxed manner:
	- `GET /api/songs/{file_path}` serves files from `backend/songs` with path traversal protection.
- Manual review listing:
	- `POST /song/manual-review` with `{ bookName, chapter, verseRange }` returns files in `songs/final_review` matching the slug pattern.
	- Response includes parsed metadata from filename and the relative path for playback.
- Frontend UI
	- Remix app provides an index/login page and a `main` route to browse/select passages (via Supabase RPC for canonical books).
	- `DisplayGeneratedSongs` component loads manual review data, streams audio via `API_SONGS_URL`, and supports review notes/status (localStorage persisted).

Acceptance Criteria
- Given files in `songs/final_review`, the manual review API returns a sorted list (most recent first) with paths that the frontend can stream.
- Frontend can play each file, change playback speed, loop, and capture approve/reject decisions locally.


## 7. Data Model (Initial)

Supabase table: `song_structure_tbl`
- `book_name` (text)
- `chapter` (int)
- `verse_range` (text)
- `song_structure` (text JSON string) — structure dict
- `tone` (int, 0=negative, 1=positive)
- `styles` (text[])

Filesystem (under `backend/songs/`)
- `pending_review/` — freshly downloaded audio
- `final_review/` — ready for human review; filenames suggested: `{slug_title}_{song_id}_{timestamp}.mp3`

Note: The frontend's `DisplayGeneratedSongs` component can parse a legacy `_index` pattern. To prevent ambiguity, the backend should standardize on the `{slug_title}_{song_id}_{timestamp}.mp3` format, and the frontend parser should be updated accordingly in a future release.


## 8. External Integrations & Constraints

- Suno website UI workflow via browser automation (Camoufox/BrowserForge). UI changes may break flows.
- Google AI (Gemini) via `middleware.gemini.model_flash` for verse ranges, structure, and reviews.
- Rate limits configured in `config/ai_review_config.py`. Default: Flash model, sequential processing.
- Frontend CORS allowed for `http://localhost:5173`. Backend served at `http://127.0.0.1:8000`.
- Environment: Windows-friendly scripts (PowerShell activation, `build.bat`).


## 9. API Contract (Current)

Base URL: `http://127.0.0.1:8000`

- `GET /` → `{ message: "server working" }`
- `GET /login` → `{ success: boolean }`
- `GET /login/microsoft` → `{ success: boolean }`

AI Generation
- `POST /ai-generation/verse-ranges` body: `{ book_name: string, book_chapter: number }` → `{ success, message, verse_ranges?: string[], error? }`
- `GET /ai-generation/verse-ranges?book_name=...&book_chapter=...` → `{ success, message, verse_ranges?: string[], error? }`
- `POST /ai-generation/song-structure` body: `{ strBookName, intBookChapter, strVerseRange, structureId? }` → `{ success, message, result?: object, error? }`

Song
- `POST /song/generate` body: `{ strBookName, intBookChapter, strVerseRange, strStyle, strTitle }` → `{ success, message, result?, error? }`
- `POST /song/download/` body: `{ strTitle?, intIndex?, download_path?, song_id? }` → `{ success, file_path?, song_title, song_index, error? }`
- `POST /song/manual-review` body: `{ bookName, chapter, verseRange }` → `{ files: { filename, parsed, path }[], total_songs, verse_reference }`

AI Review
- `POST /ai_review/review/` body: `{ audio_file_path, pg1_id }` → `{ success, verdict, first_response?, second_response?, audio_file?, deletion_message?, move_message?, error? }`

Orchestrator
- `POST /orchestrator/workflow` body: `{ strBookName, intBookChapter, strVerseRange, strStyle, strTitle, song_structure_id? }` → `{ success, message, total_attempts, final_songs_count, good_songs?, re_rolled_songs?, workflow_details?, error? }`
- `POST /orchestrator/debug/download` body: `{ title, temp_dir? }` → debug response
- `POST /orchestrator/debug/review` body: `{ audio_file_path, pg1_id }` → debug response

Streaming
- `GET /api/songs/{file_path}` → streams audio under `backend/songs` with content-type and range headers.


## 10. End-to-End Workflow

1) Operator selects Book/Chapter → generate/get verse ranges → choose a range.
2) Request song structure for the passage; tone and styles computed and stored.
3) Start orchestrator with `{ Book, Chapter, VerseRange, Style, Title }`.
4) Orchestrator: generate 2 songs → wait → download both → AI review each → if `re-roll`, repeat up to 3 attempts → move final artifacts to `final_review`.
5) Frontend manual review loads files via `/song/manual-review`, plays via `/api/songs/...`, reviewer sets status/notes; final decision remains manual.


## 11. Non-Functional Requirements (NFRs)

Reliability & Resilience
- Orchestrator never ends with zero outputs; the last attempt’s artifacts are moved to `final_review` regardless of AI verdict.
- Clear error messages and HTTP status codes.

Performance & Throughput
- Respect rate limits (default sequential processing). Target: reliably handle 3 attempts per passage without quota errors.

Security
- CORS restricted to known origins. Path traversal protected in streaming endpoint.
- Secrets in `.env`; do not log credentials or tokens.

Observability
- Centralized logging for AI generations with daily log files. Future: structured JSON logs and rotation.

Compatibility
- Windows-first local dev (PowerShell venv activation instructions included).


## 12. Risks, Assumptions, and Mitigations

Risks
- Suno UI changes break automation. Mitigation: encapsulated actions (e.g., `utils/camoufox_actions.py`), regular maintenance.
- AI rate limit changes or outages. Mitigation: config-driven delays, sequential default, potential queue/backoff.
- Filename format inconsistencies between backend and frontend parsing. Mitigation: define and enforce a single canonical filename pattern and update both ends.
- Missing or outdated endpoints in the frontend (e.g., legacy `/download-song`). Mitigation: deprecate/remove old calls and centralize API utilities.

Assumptions
- Two variants per Suno generation request; negative indexing (-1, -2) retrieves the latest outputs.
- Supabase schema `song_structure_tbl` exists with the fields used by the backend.


## 13. Success Metrics / KPIs

- Generation Success Rate: ≥ 90% of orchestrator runs end with ≥ 1 artifact in `final_review`.
- Review Efficiency: ≥ 50% of outputs pass AI review on first attempt over time.
- Manual Review Time: median < 3 minutes per passage to audition and decide.
- Stability: < 2% runs fail due to automation errors (selectors, timing, etc.) over 7 days.


## 14. Release Plan

MVP (v0.9)
- Login flows working, verse-range + structure generation stored to Supabase.
- Manual trigger for generation, manual download possible, basic manual review page streams audio.

v1.0
- Orchestrator end-to-end (3 attempts, AI review, file moves), streaming endpoint hardened, manual review flow finalized.
- Frontend uses `/song/download/` and `/song/manual-review` only; remove/deprecate legacy `/download-song` usage.

v1.1
- Persist manual review decisions (approved/rejected/notes) to Supabase; expose API for listing curated outputs.
- Unify filename format and add backend validation of names; provide a small metadata JSON per file.
- Structured logging and metrics endpoints.


## 15. Open Questions

- Should review decisions be persisted immediately or batched? Which table schema to use for manual reviews?
- How should we handle titles/styles provenance for downstream catalogs? Store alongside audio metadata?
- Do we need a queue/worker pattern for batch runs or concurrency beyond sequential?
- Any need for user auth/roles on the frontend beyond local use?


## 16. Acceptance Criteria Summary (by Capability)

- Suno Login: `/login` and `/login/microsoft` return `{ success }` and enable navigation to `/main` on success.
- AI Generation: `/ai-generation/*` endpoints populate `song_structure_tbl` and return structured responses.
- Song Generation: `/song/generate` returns success and logs; produces two variants per attempt.
- Download: `/song/download/` downloads and returns a valid file path; negative indexing supported.
- AI Review: `/ai_review/review/` returns a verdict with details; respects delay config.
- Orchestrator: `/orchestrator/workflow` returns aggregated result metrics; ensures artifacts end in `final_review`.
- Streaming: `/api/songs/{file_path}` streams audio within the sandbox; prevents path traversal.
- Manual Review: `/song/manual-review` returns files for the specified passage; frontend streams and allows status/notes.


## 17. Glossary

- Verse Range: A contiguous set of verses within a chapter (e.g., `1-11`).
- Song Structure: Map of song sections to verse ranges (e.g., `{ "verse1": "1-5", "chorus": "6-8" }`).
- Re-roll: Re-generate songs due to low quality or failed review.
- Final Review: Human approval stage prior to distribution or archival.


## 18. Appendix: Notable Files

- Backend
	- `backend/main.py` — FastAPI app, CORS, routers.
	- `backend/api/ai_generation/routes.py` — verse ranges & song structure endpoints.
	- `backend/api/ai_review/routes.py` — AI review endpoint.
	- `backend/api/song/routes.py` — song generate/download/manual-review endpoints.
	- `backend/routes/songs.py` — secure streaming endpoint.
	- `backend/config/ai_review_config.py` — review rate limits/model config.
- Frontend
	- `frontend/app/routes/_index.tsx` — landing/login page.
	- `frontend/app/routes/main.tsx` — main browser for canonical books.
	- `frontend/app/components/DisplayGeneratedSongs.tsx` — manual review player UI.
	- `frontend/app/lib/api.ts` — frontend API helpers for backend endpoints.

