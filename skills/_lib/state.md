# `private/state.json` schema and mutation rules

The state file is the single source of truth for "what's @omgjlk doing right
now and recently?". It lives at `private/state.json`. It is gitignored.

## Schema

```json
{
  "active_tasks": ["<task-id>", "..."],
  "focus": "<task-id> or null",
  "paused_tasks": ["<task-id>", "..."],
  "recent_completed": [
    {"id": "<task-id>", "title": "...", "completed_at": "<ISO-8601>"}
  ],
  "tasks": {
    "<task-id>": {
      "title": "<short human title>",
      "started_at": "<ISO-8601>",
      "last_touched_at": "<ISO-8601>",
      "status": "in_progress | paused | done",
      "kind": "issue | pr-review | doc-review | investigation | meeting-followup | slack-thread | other",
      "board_item_id": "PVTI_...",
      "board_item_number": 1234567890,
      "issue": "owner/repo#NN or null",
      "pr": "owner/repo#NN or null",
      "links": ["https://...", "..."],
      "copilot_session_ids": ["uuid", "..."],
      "touches": [
        {"at": "<ISO-8601>", "via": "start | switch | note | copilot-session | slack-review | manual", "note": "optional"}
      ],
      "internal_notes_path": "private/tasks/<task-id>/notes.md"
    }
  }
}
```

## Invariants

1. **`active_tasks` is a set.** Each task-id appears at most once. Order is
   not meaningful (treat it as a set when comparing; it's a JSON array only
   for serialization).
2. **`focus` is always either `null` or an element of `active_tasks`.** Never
   point `focus` at a paused or done task. On `pause-task` of the focus
   task, set `focus` to `null` (or to another active task if the caller
   passes one).
3. **A task-id appears in exactly one of `active_tasks`, `paused_tasks`, or
   (via `recent_completed[].id`) the recent-done list.** Never two.
4. **`recent_completed` is capped at 50 entries.** Older entries fall off
   (state file is not a long-term audit log; the board and GitHub issues
   are). Most-recent first.
5. **`touches` is append-only within a session.** It is the audit trail for
   the daily-summary skill.

## Task IDs

`YYYY-MM-DD-<slug>` where `<slug>` is a 2–4 word kebab-case description.
Examples: `2026-05-21-bootstrap-waddy`, `2026-05-21-review-auth-pr`.

If the same day produces two tasks with the same slug, append `-2`, `-3`.

## Mutation discipline

- **Always read the whole file, mutate in memory, write the whole file.** No
  partial updates. The file is small; atomicity is more important than IO.
- **Write via temp-file + rename** to avoid corrupting state if the process
  dies mid-write:
  ```bash
  jq '...' private/state.json > private/state.json.tmp && \
    mv private/state.json.tmp private/state.json
  ```
- **Update `last_touched_at` on EVERY mutation to the task**, including
  `touch-task` and `switch-to`.
- **`switch-to <id>`** mutates only `focus` and the target task's
  `last_touched_at` + a `{via: "switch"}` entry in `touches`. It does NOT
  move the task between `active_tasks`/`paused_tasks` and does NOT touch
  the board.

## First-run bootstrap

If `private/state.json` doesn't exist when a skill is invoked, create it with:

```json
{
  "active_tasks": [],
  "focus": null,
  "paused_tasks": [],
  "recent_completed": [],
  "tasks": {}
}
```

If `private/config.json` doesn't exist either, halt and walk the user through
setup (copy `private/config.example.json`).
