---
name: pause-task
description: >
  Explicitly pause a task (status → Paused on the board, move from
  `active_tasks` to `paused_tasks` in state). Use for "I'm setting this
  aside for hours or days". Not for minute-by-minute context switching —
  use `switch-to` for that.
---

# pause-task

Trigger phrases: "pause …", "set aside …", "park …", "stash …",
"I'm putting … on hold".

## Input

Optional task identifier (same resolution as `switch-to`). If omitted,
default to `focus`.

## Steps

1. Read `private/state.json` and `private/config.json`.
2. Resolve input → task-id.
3. If task isn't currently `in_progress`, tell the user and ask whether
   they meant something else (e.g. `complete-task`). Don't silently no-op.
4. Update the board:
   - `update_project_item` setting `Status` →
     `board.status_options.paused`.
5. Mutate state.json:
   - Remove `<task-id>` from `active_tasks`.
   - Append `<task-id>` to `paused_tasks` (idempotent).
   - `tasks[<task-id>].status = "paused"`
   - `tasks[<task-id>].last_touched_at = now`
   - Append `{at: now, via: "manual", note: "paused"}` to `touches`.
   - If `focus == <task-id>`: set `focus` to `null`, and tell the user.

6. Reply:
   ```
   ⏸  Paused: <title>
      Active tasks remaining: <N>
   ```

   If `focus` was cleared, ask:
   > "Focus is now unset. Want to switch focus to one of your active
   > tasks? (1) <title1>  (2) <title2>  …"

## What this skill MUST NOT do

- Auto-move any other task into focus.
- Delete the board item.
- Touch tasks other than the target.
