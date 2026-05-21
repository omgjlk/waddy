---
name: touch-task
description: >
  Record that work happened on a task without changing its status or focus.
  Used by both the user ("I just had a 10-minute conversation in Slack
  about task X") and by observers (slack-review, inspect-sessions) to leave
  an audit trail that `daily-summary` can reason about.
---

# touch-task

Trigger phrases: "I worked on …", "touch …", "log time on …",
"note progress on …".

## Input

- A task identifier (required, same resolution as `switch-to`).
- An optional free-text note (will be stored in the touch entry).
- An optional `via` source (default `"manual"`; observers pass their own).

## Steps

1. Read `private/state.json`.
2. Resolve → task-id.
3. If task is not in `active_tasks` AND not in `paused_tasks`:
   - If it's in `recent_completed`: warn ("that task is done") and ask if
     the user wants to reopen via `resume-task`. Don't silently re-add.
   - If unknown: ask.
4. Mutate state.json:
   - `tasks[<task-id>].last_touched_at = now`
   - Append `{at: now, via: "<via>", note: "<note?>"}` to `touches`.
5. Reply (one line):
   ```
   ✏️  Touched <task-id> — <note or "noted">
   ```

## What this skill MUST NOT do

- Change `status`.
- Change `focus`.
- Touch the board.
