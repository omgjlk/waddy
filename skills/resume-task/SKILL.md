---
name: resume-task
description: >
  Resume a paused task. Moves it from `paused_tasks` back to `active_tasks`,
  sets the board status back to "In progress", and makes it the current
  `focus`. Other active tasks are untouched.
---

# resume-task

Trigger phrases: "resume …", "pick back up …", "un-pause …",
"continue …".

## Input

Optional task identifier. If omitted:
- If `paused_tasks` has exactly one entry, use it.
- Else list paused tasks and ask which to resume.

## Steps

1. Read `private/state.json` and `private/config.json`.
2. Resolve → task-id.
3. If task isn't in `paused_tasks`:
   - In `active_tasks`: tell the user it's already active; offer `switch-to`.
   - In `recent_completed`: ask whether to reopen as a new task (don't
     silently re-add a completed item).
4. Update the board:
   - `update_project_item` setting `Status` →
     `board.status_options.in_progress`.
5. Mutate state.json:
   - Remove `<task-id>` from `paused_tasks`.
   - Add to `active_tasks` (idempotent set).
   - `tasks[<task-id>].status = "in_progress"`
   - `tasks[<task-id>].last_touched_at = now`
   - Append `{at: now, via: "manual", note: "resumed"}` to `touches`.
   - Set `focus = "<task-id>"`.
6. Reply:
   ```
   ▶️  Resumed: <title>
      Focus → <title>
      Active tasks: <N>
   ```

## What this skill MUST NOT do

- Pause any other task to "make room" — the user can have many active
  tasks. Do not auto-balance.
