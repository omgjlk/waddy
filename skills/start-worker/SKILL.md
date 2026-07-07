---
name: start-worker
description: >
  Package an existing waddy task for a SEPARATE Copilot session to execute and
  hand back. Produces a self-contained worker briefing (goal, links, notes path,
  and the exact Handoff block to append), copies it to the clipboard for the user
  to paste into a fresh `copilot` session, and arms waddy to expect a handoff.
  Does NOT do the work and does NOT pause the task.
---

# start-worker

Read `_lib/handoff.md` and `_lib/state.md` first. This is the dispatch half of
the handoff loop; the `handoff` skill is the return half.

Trigger phrases: "hand this off to a worker", "dispatch <task> to another
session", "make a worker brief for …", "I'll work <task> in another session",
"prep <task> for a worker".

## Mental model

A worker session (often in a different repo) has **no waddy context** — no skills,
no `state.json`, no conventions. So the briefing must be **fully self-contained**:
inline the goal, the links, the absolute notes path, and the literal Handoff
block. The worker's only reporting step is appending that block; waddy correlates
and closes later (via `handoff` + the session ledger).

## Steps

1. **Load context.** Read `private/config.json` and `private/state.json`
   (`_lib/state.md`). Read `_lib/handoff.md` and `templates/worker-brief.md`
   if not in context.

2. **Identify the target task.** From the user's reference (task-id, issue/PR,
   or description) find the task in `state.json`.
   - If no matching task exists, offer to run `start-task` first, then continue.
   - Do **not** change the task's status or focus, and do **not** pause it.

3. **Gather briefing inputs.**
   - `title`, `task_id` from the task.
   - `goal`: the concrete work + acceptance criteria. Pull from the task's notes
     / issue; if unclear, ask the user for a one-paragraph goal.
   - `links`: task `links` + `issue`/`pr` (as URLs).
   - `notes_path`: the task's `internal_notes_path`, resolved to an **absolute**
     path (e.g. `~/src/waddy/private/tasks/<id>/notes.md` → expand `~`) so a
     worker in another repo can find it.
   - `repo`: where the work runs. Infer from the issue/PR repo or ask; express as
     a clone path or `owner/repo`.

4. **Ensure the notes file exists.** If `internal_notes_path` is missing, create
   `private/tasks/<task-id>/notes.md` with a `## Initial dump` heading (same as
   `start-task` step 8) so the worker has a file to append to.

5. **Render the briefing.** Fill `templates/worker-brief.md` with the inputs.
   The template already inlines the literal Handoff block and the notes path —
   keep it self-contained; do not replace inlined content with references to
   waddy internals. Keep the `<!-- waddy-task: <id> -->` marker near the top:
   when the user pastes the brief as the worker's first prompt, the
   `userPromptSubmitted` ledger hook records a **claim** entry binding that
   session to the task, at pickup time (survives a crash before any handoff).

6. **Deliver.**
   - Copy the rendered briefing to the clipboard (`pbcopy`).
   - Also write it to `private/tasks/<task-id>/worker-brief.md` for the record.

7. **Arm waddy.** Add a `touches[]` entry to the task:
   `{at: now, via: "handoff-requested", note: "dispatched to worker (<repo>); awaiting handoff"}`
   and bump `last_touched_at`. This lets `morning-brief` / `handoff` flag the
   task as "out with a worker, no handoff yet." Optionally record the target repo
   so the session ledger can be joined by repo/time to find the worker session.

8. **Confirm to the user.** Reply with:
   ```
   📦 Worker brief ready for: <title>   (task <task-id>)
      Copied to clipboard + saved to private/tasks/<task-id>/worker-brief.md
      → open a new terminal:  cd <repo> && copilot   then paste.
      I'll watch for the handoff (run `waddy process handoffs` later, or it
      surfaces in your morning brief).
   ```

## What this skill MUST NOT do

- Do the work itself (it only packages it).
- Pause the task or change its status/focus (multi-active is the norm).
- Commit or write any file outside `private/` (plus the clipboard).
- Reference waddy-internal context the worker can't act on — the brief is
  self-contained by design.

## Relationship to other skills

- `handoff` (Mode A) — what the worker does at the other end.
- `handoff` (Mode B) — waddy reads the returned block and closes/unblocks.
- session ledger (`tools/session_ledger.py`) — deterministically records the
  worker session by repo/time for correlation.
