# Deletion Logic Migration Plan

System: Suno Automation  
Module: Orchestrator Deletion Logic  
Purpose: Adopt `backend/utils/delete_song.py` for centralized deletion when handling re-roll verdicts in the orchestrator.

## Objective
- Replace direct `os.remove` calls during non-final attempts with the reusable deletion utility to centralize logic and improve resilience and traceability.
- Preserve existing final-attempt behavior (no deletion; preserve for fail-safe).
- Avoid changing public interfaces or workflow return shapes.

## Current Behavior (reference)
- Documented in `backend/api/orchestrator/RE-ROLL-DELETION.md`.
- Non-final attempts: `process_song_verdicts` deletes re-roll files using `os.remove(file_path)`.
- Final attempt: `process_song_verdicts_final_attempt` preserves re-roll files (no deletion) for fail-safe.

## Proposed Change (Minimum Viable)
- Use `SongDeleter.delete_local_file(file_path)` from `backend/utils/delete_song.py` for re-roll deletions in non-final attempts.
- Do not alter final-attempt logic (still preserve re-roll files).
- Keep function contracts and returned dicts unchanged.
 - When a `song_id` is available in the workflow context, REMOTELY DELETE the song on Suno in addition to deleting the local copy. Remote deletion is mandatory (not optional) for re-roll verdicts when the Suno `song_id` exists.
 - Remote deletion is mandatory: the orchestrator MUST delete the song on Suno for any `re-roll` verdict. Therefore, a `song_id` is REQUIRED whenever the orchestrator attempts to delete a re-rolled song. If a `song_id` is not available in the workflow context for a re-roll, the orchestrator should return an error instead of proceeding with a local-only deletion.

## Implementation Steps
1. Import utility in orchestrator:
   - `from backend.utils.delete_song import SongDeleter`
2. Update `process_song_verdicts` only (non-final path):
   - Replace the `os.remove(file_path)` block with:
     ```python
     deleter = SongDeleter()
  # song_id is required for re-roll deletions (remote deletion is mandatory)
  song_id = result.get("song_id") or result.get("songId") or None
  if not song_id:
    # Requirement: cannot perform a re-roll deletion without a Suno song_id
    error_msg = f"Missing song_id for re-roll deletion of {file_path}"
    print(f"[VERDICT] ❌ {error_msg}")
    # Return or raise as appropriate for the orchestrator flow — the plan requires returning an error
    return {"success": False, "error": error_msg, "kept_count": kept_count, "deleted_count": deleted_count}

  # Perform mandatory remote+local deletion when song_id exists
  delete_result = await delete_song(song_id=song_id, file_path=file_path, delete_from_suno=True)
  # Consider deletion successful if either local or remote deletion succeeded
  if delete_result.get("local_deleted") or delete_result.get("suno_deleted") or delete_result.get("success"):
    deleted_count += 1
  else:
    print(f"[VERDICT] Delete failed: {delete_result.get('errors', delete_result.get('error', 'unknown error'))} for {file_path}")
     ```
3. Leave `process_song_verdicts_final_attempt` unchanged (no deletions on final attempt).
4. Logging: retain existing orchestrator logs; the utility already logs file and directory cleanup.
5. Documentation: update `RE-ROLL-DELETION.md` to note the centralized deletion utility now handles local deletion on non-final attempts.

## Remote deletion (REQUIRED when `song_id` available)
- Remote deletion support (Suno) is REQUIRED: when a `song_id` is available in the workflow context, the orchestrator MUST call the centralized helper to delete the song on Suno as well as remove the local copy. Example:
  ```python
  from backend.utils.delete_song import delete_song
  # song_id should be threaded into review_results/download entries so it's available here
  delete_result = await delete_song(song_id=song_id, file_path=file_path, delete_from_suno=True)
  ```
- Thread `song_id` through `download_both_songs` -> `review_all_songs` -> `process_song_verdicts` so each `result` may include an optional `c` field. When present, remote deletion MUST be attempted.
- Recommended safety: although remote deletion is mandatory when `song_id` exists, you may still use an env var or rollout flag (e.g. `DELETE_FROM_SUNO_ENABLED`) during initial deployment to control activation across environments — but the long-term behavior in the codebase is that remote deletion is performed whenever a `song_id` is known.

## Data/Interface Impact
- No changes to orchestrator inputs/outputs.
- Maintain return structure of `process_song_verdicts` and `process_song_verdicts_final_attempt`.

## Testing Plan
- Unit tests for `process_song_verdicts`:
  - Approved path moves to `final_dir` (existing behavior).
  - Re-roll path calls utility; increments `deleted_count` on success, logs on failure.
  - When `song_id` is present, the orchestrator must call `delete_song(..., delete_from_suno=True)` and treat deletion as successful if local or remote deletion succeeded.
  - Simulate remote deletion success and failure cases; ensure failures are logged and do not stop processing of other items.
- Smoke test the full workflow to ensure totals and messages are unchanged.

## Risks and Mitigations
- Utility deletion failure: handled per-file; loop continues; error logged.
- Behavior drift: final-attempt logic intentionally untouched.
 - Remote deletion failures (browser automation, network): must be logged per-file. Since remote deletion is mandatory when `song_id` is available, design must ensure failures do not break the overall workflow; consider retries or a background compensating job to clean up remaining Suno entries.
 - Safety during rollout: recommended to use an env var during early rollout to enable or disable the remote step per environment. This is a deployment control only — functional requirement remains mandatory.

## Rollout
- Single small patch to `backend/api/orchestrator/utils.py`.
- No configuration changes required for the MVA.
 - Small patch to `backend/api/orchestrator/utils.py` to replace direct `os.remove` calls with the centralized deletion flow including `delete_song` when `song_id` exists.
 - Consider a short-lived env var or feature flag to control activation during deployment, but code must perform remote deletion when `song_id` is present.

## Future Enhancements
- Archive instead of delete: move re-roll files to `archive/` or `trash/` instead of permanent deletion.
- Structured logging (JSON) with decision context for auditability.
- Add tests for final-attempt preservation + fail-safe flow.

