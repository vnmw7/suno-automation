"""
System: Suno Automation
Module: Orchestrator CDN Download Plan
File URL: docs/ORCHESTRATOR_CDN_DOWNLOAD_PLAN.md
Purpose: Define implementation steps for adding CDN-based song downloads while preserving legacy flow.
"""
Plan Name: Direct CDN Download Flow Integration

Before you respond, develop an internal rubric for what defines a "world-class" and "industry-standard" answer to my request (task, analysis, or problem solving). Then internally iterate and refine the draft until it scores top marks against your rubric. Provide only the final perfected output. Always provide a comprehensive and detailed breakdown. Always think hard about the given topic, problem, and the solution. Always flag the responses that you are not confident about so that I can research it further. Always use industry standard, best practices, and professional recommendations when programming. Always search and use the latest documentations and information regarding programming technologies as of the date of the conversation. Always ask for further clarifications whenever requirements, constraints, or expectations are unclear instead of relying on assumptions.

Context Summary:
- Repository areas: `backend/api/orchestrator/utils.py`, potential helper placement in `backend/api/orchestrator/` or `backend/api/song/` utilities.
- Key constraints: Maintain Minimum Viable Approach, keep existing `download_both_songs` behaviour for UI-driven fallback, respect Result-pattern dict structure (`{"success": bool, ...}`), retain file headers, honour naming-prefix guidance while prioritising local snake_case consistency, and avoid breaking orchestrator workflow retries.
- Design decisions: Use `aiohttp` for non-blocking CDN downloads to match the async orchestrator; adopt `{song_id}.mp3` filenames within the existing pending/failsafe directories unless conflict detected.

Current Implementation Snapshot:
- Target region `backend/api/orchestrator/utils.py:287-358` to remain available as legacy fallback:
```
async def download_both_songs(title: str, temp_dir: str, song_ids: list = None) -> Dict[str, Any]:
    try:
        from utils.download_song_v2 import download_song_v2
        downloaded_songs = []
        download_1 = await download_song_v2(
            strTitle=title,
            intIndex=-1,
            download_path=temp_dir,
            song_id=first_song_id
        )
        download_2 = await download_song_v2(
            strTitle=title,
            intIndex=-2,
            download_path=temp_dir,
            song_id=second_song_id
        )
        return {"success": True, "downloads": downloaded_songs, "message": f"Downloaded {len(downloaded_songs)} of 2 songs"}
    except Exception as e:
        return {"success": False, "error": f"Download process failed: {str(e)}", "downloads": []}
```

New Helper Contract (`downloadSongsFromCdn`):
```
# Success
{
    "success": True,
    "song_id": "<uuid>",
    "file_path": "backend/songs/pending_review/<uuid>.mp3",
    "message": "Downloaded from CDN"
}

# Failure
{
    "success": False,
    "song_id": "<uuid>",
    "error": "HTTP 404: Not Found"
}
```

Assumptions:
- CDN endpoint `https://cdn1.suno.ai/{song_id}.mp3` remains publicly accessible without authentication once generation completes.
- Song IDs in `generation_result['result']['song_ids']` map one-to-one with downloadable audio assets.
- Existing pending/fail-safe directory semantics (`backend/songs/pending_review`) must not change during rollout.

Task Steps:
1. Discovery – Catalogue any current helper that already hits CDN assets (check `utils/download_song_v2.py`, `backend/configs/suno_selectors.py`) and confirm whether orchestration expects waveform downloads or lyric metadata. Deliverable: short note in plan comments clarifying available tooling. Confidence: Medium.
2. Design – Document CDN-first flow inside `backend/api/orchestrator/utils.py`, including timeout policy (~30s), retry count (single attempt per ID before falling back), and filename-collision handling (append timestamp suffix when file exists). Deliverable: inline design comment block. Confidence: Medium.
3. Environment Prep – Activate `backend\.venv` and install dependencies with `backend\.venv\Scripts\python -m pip install --upgrade aiohttp mutagen`; verify import success and record commands. Update dependency documentation or requirements file if applicable. Confidence: High.
4. Implementation – Introduce async helper `downloadSongsFromCdn` that uses `aiohttp.ClientSession` with streamed writes, validates MP3 via simple header check (ensure bytes start with `ID3` or `0xFFFB`), applies Result-pattern response, and preserves snake_case naming. Deliverable: helper with docstring and minimal logging. Confidence: Medium.
5. Implementation – Refactor `download_both_songs` to orchestrate hybrid flow:
   - Initialise `downloaded_songs`, `cdn_failures`, and `missing_ids`.
   - If `song_ids` present, iterate per ID, call CDN helper, record successes, and collect failures.
   - For each failed ID (or when no IDs provided), fall back to `download_song_v2` using existing indices while preserving legacy behaviour.
   - Merge results, avoid duplicate entries, and maintain existing return schema/log messaging. Document naming-convention exception rationale in-line. Confidence: Medium.
6. Validation – Implement unit tests for `downloadSongsFromCdn` covering success, 404, 500, timeout, and corrupted-MP3 scenarios (use pytest + aiohttp test utilities). Add integration test exercising hybrid flow (mock CDN response then legacy fallback). Execute `backend\.venv\Scripts\ruff check`, run targeted pytest suite (e.g., `backend\.venv\Scripts\python -m pytest backend/api/orchestrator/tests/test_utils.py`), confirm `aiohttp` and `mutagen` availability via `backend\.venv\Scripts\python -c "import aiohttp, mutagen"`, and perform manual smoke by downloading a known song ID with `mutagen` quick load. Deliverable: recorded command outputs or links. Confidence: Medium.
7. Documentation & Wrap-up – Update README or operator guide if manual steps change, note hybrid-flow addition in changelog, and document testing evidence. Deliverable: doc updates or confirmation none required. Confidence: High.

Validation Checklist:
- Variable prefixes and naming follow repository guidance or include comment documenting local snake_case consistency.
- All new/edited files retain required headers.
- CDN helper writes `.mp3` files, confirms integrity (>0 bytes and signature check), and cleans up partial downloads on failure.
- Legacy Selenium/selector flow remains callable via `download_song_v2` fallback.
- Dependencies installed inside `backend\.venv` and verified via import check.
- Tests executed: unit tests for CDN helper, integration test for hybrid flow, `ruff check`, manual smoke with `mutagen` verification.

Risks & Mitigations:
- Naming convention conflict with repository standards; mitigate by documenting adherence to local snake_case and proposing follow-up refactor if needed.
- CDN availability or rate limits causing partial downloads; mitigate with timeout handling, informative error messages, and reliable fallback.
- Duplicate filenames when repeated song IDs used; mitigate by timestamp suffix policy and documenting behaviour.
- Virtual environment drift if dependencies omitted; mitigate by executing Step 3 and capturing commands in documentation.

Confidence Assessment:
- Overall confidence: Medium-High – decisive design choices, explicit contracts, and expanded validation reduce ambiguity while acknowledging dependency and naming risks.
