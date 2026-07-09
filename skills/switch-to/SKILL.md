---
name: switch-to
description: >
  Soft focus change. Updates the `focus` pointer in `private/state.json`
  and records a touch on the target task. No waddy `status` changes. The only
  board write is promoting the focus target's card from To do → In progress
  (if it's a public, on-board, To-do item). Designed for the rapid
  context-switching that happens every few minutes — between an in-flight
  Copilot CLI session, Slack, and email.
---

# switch-to

Trigger phrases: "switch to …", "I'm now on …", "focus on …", "looking at … now".

## Why this skill exists

The user multitasks and switches attention constantly. Promoting every
micro-switch to a "paused / in-progress" board churn would be exhausting
and useless. `switch-to` is the lightweight pointer move that lets
`daily-summary` and `status` accurately reflect where attention is right
*now* without ceremony.

## Input

A task identifier — one of:
- A task-id (`YYYY-MM-DD-<slug>`)
- A board item URL or issue/PR URL → resolve to task-id via state's
  `tasks[*].issue|pr|board_item_id` fields
- A fuzzy title match → if ambiguous, list candidates and ask

## Steps

1. Read `private/state.json`.
2. Resolve the input to a task-id.
3. If the task is not in `active_tasks`:
   - If it's in `paused_tasks`: ask:
     > "That task is paused. Resume it (status → In progress) or just
     > switch focus without changing status?"
     - "Resume" → invoke `resume-task` skill instead.
     - "Just focus" → unusual; allow it but warn that the board still
       shows Paused. Proceed.
   - If it's in `recent_completed` or unknown: ask whether to start a new
     task. Don't silently re-open.
4. Mutate state.json:
   - `focus = "<task-id>"`
   - `tasks[<task-id>].last_touched_at` = now
   - Append `{at: now, via: "switch"}` to `tasks[<task-id>].touches`
5. **One narrow board write (only this):** if the target is `public`, has a
   `board_item_id`, and its card is currently **To do**, promote it **To do →
   In progress** (`update_project_item` → `board.status_options.in_progress`).
   This satisfies "mark it in progress when I start working on it" for items
   pulled off the backlog. Do **nothing** to the board in any other case (a card
   already In progress/Paused/Done is left as-is; private tasks have no card).
6. Reply with a one-liner:
   ```
   👀 Focus → <title> (task <task-id>)
   ```

## What this skill MUST NOT do

- Change any task's `status` in state.json (the board To do→In progress
  promotion in step 5 is a board-only nicety; it does not rewrite the waddy
  `status`, which `start-task`/`resume-task` own).
- Touch the board beyond the single To do→In progress promotion of the focus
  target described in step 5.
- Modify any task other than the target.
