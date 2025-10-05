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
- Key constraints: Maintain Minimum Viable Approach, keep existing `download_both_songs` behaviour for UI-driven fallback, respect Result-pattern dict structure (`{"success": bool, ...}`), retain file headers, honour naming-prefix guidance despite current snake_case usage, and avoid breaking orchestrator workflow retries.
- Open questions: Should new CDN downloader prefer async streaming via `aiohttp` or reuse existing sync tooling? Confirm acceptable filename schema when saving `{song_id}.mp3` alongside legacy-named files.

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

Assumptions:
- CDN endpoint `https://cdn1.suno.ai/{song_id}.mp3` remains publicly accessible without authentication once generation completes.
- Song IDs in `generation_result['result']['song_ids']` map one-to-one with downloadable audio assets.
- Existing pending/fail-safe directory semantics (`backend/songs/pending_review`) must not change during rollout.

Task Steps:
1. Discovery – Catalogue any current helper that already hits CDN assets (check `utils/download_song_v2.py`, `backend/configs/suno_selectors.py`) and confirm whether orchestration expects waveform downloads or lyric metadata. Deliverable: short note in plan comments clarifying available tooling. Confidence: Medium.
2. Design – Draft a minimal flow that attempts CDN download first when `song_ids` exists, then gracefully reverts to UI automation (`download_song_v2`). Define filename convention (e.g., `{song_id}.mp3`) and ensure storage respects existing directory structure. Deliverable: commented design block within code prior to implementation. Confidence: Medium.
3. Implementation – Add new async helper (e.g., `downloadSongsFromCdn`) under `backend/api/orchestrator/utils.py` or adjacent module, encapsulating HTTP GET with streamed write to MP3, using Result-pattern dict response and variable prefixes per guidelines. Preserve legacy logic by invoking helper from `download_both_songs` and only falling back to legacy path on failure. Deliverable: new helper function with docstring and unit-level comments. Confidence: Medium.
4. Implementation – Refactor `download_both_songs` to orchestrate hybrid flow: check CDN success for each `song_id`, accumulate successes, and call legacy downloads only for missing assets or when IDs absent. Ensure workflow metrics still count downloads correctly and maintain backwards compatibility for callers expecting `downloaded_songs` entries. Deliverable: updated function body with clear branching and logging. Confidence: Low (risk of tightening naming conventions in existing snake_case region).
5. Validation – Run applicable checks (`npm run lint`, `npm run typecheck` if JS touched, `ruff check` for Python style) and perform manual download dry-run (simulate by calling helper with known song_id) to verify saved MP3 integrity and fallback behaviour. Deliverable: recorded command outputs or notes. Confidence: Medium.
6. Documentation & Wrap-up – Update relevant README or workflow docs if operator instructions change, and summarize behaviour change in changelog if required. Deliverable: doc updates or confirmation none required. Confidence: High.

Validation Checklist:
- Variable prefixes and naming follow repository convention or document deviations with rationale.
- All new/edited files retain required headers.
- CDN downloader writes `.mp3` files and validates via simple size > 0 check before success flag.
- Legacy Selenium/selector flow remains callable by retaining `download_song_v2` usage.
- Commands executed: `ruff check`, targeted async download smoke test script (documented).

Risks & Mitigations:
- Naming convention conflict with existing snake_case Python code; mitigate by requesting guidance or documenting exception if adherence breaks compatibility.
- CDN availability or rate limits causing partial downloads; mitigate with timeout handling and fallback to legacy method.
- Duplicate filenames when multiple attempts use same song_id; include timestamp or title suffix in CDN saver if required.

Confidence Assessment:
- Overall confidence: Medium – new network path introduces variability and coding standards diverge from legacy patterns; expect targeted testing and potential follow-up clarification on naming rules.
