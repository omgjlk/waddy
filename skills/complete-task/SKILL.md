---
name: complete-task
description: >
  Mark a task done. Sets the board status to "Done", removes the task from
  `active_tasks` / `paused_tasks`, and adds an entry to `recent_completed`.
  Optionally prompts the user for a one-line outcome to capture before the
  task drops off the active set.
---

# complete-task

Trigger phrases: "finished …", "done with …", "completed …",
"mark … done", "ship …", "wrap up …".

## Input

Optional task identifier. If omitted, defaults to `focus`.

## Steps

1. Read `private/state.json` and `private/config.json`.
2. Resolve → task-id.
3. Capture an outcome line. Ask:
   > "One-line outcome for the daily summary? (or hit enter to skip)"

   Store the answer (if any) in
   `tasks[<task-id>].outcome` and append a `{via: "manual", note: "<outcome>"}`
   touch.
4. Update the board:
   - `update_project_item` setting `Status` → `board.status_options.done`.
5. Mutate state.json:
   - Remove from `active_tasks` AND `paused_tasks`.
   - `tasks[<task-id>].status = "done"`
   - `tasks[<task-id>].last_touched_at = now`
   - Prepend to `recent_completed`:
     `{id, title, completed_at: now}` and truncate the list to 50 entries.
   - If `focus == <task-id>`: set `focus = null` and ask the user if they
     want to switch focus to another active task (offer choices).
6. Reply:
   ```
   ✅ Done: <title>
      Outcome: <outcome or "—">
      Active tasks remaining: <N>
   ```

## What this skill MUST NOT do

- Close the backing issue or PR. That's the user's decision — completing a
  task on the waddy board is not the same as closing the underlying GitHub
  artifact. (We may add a "and close the issue?" prompt in a future
  revision; for now, never auto-close.)
- Remove the board item. "Done" stays on the board for visibility.
