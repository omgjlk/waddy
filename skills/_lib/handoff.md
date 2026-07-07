# Cross-session handoff convention

The mechanism that lets one Copilot session hand work to another and get the
result back **without introspecting the other session's transcript**. The
channel is a plain file plus an append-only, greppable block — authoritative
because the worker *declares* what it did, rather than waddy reverse-engineering
intent from a compacted log.

Referenced by: `handoff` (both directions), `start-task` (hand a task off),
`complete-task` (a `ready-to-close` handoff arrives).

## The channel

Each task's canonical notes file: `private/tasks/<task-id>/notes.md` (the value
of the task's `internal_notes_path` in `state.json`). This is the shared
substrate:

- **waddy** (this agent) creates the task + notes file and hands the worker a
  pointer to it.
- **A worker session** (any Copilot CLI session, in any repo) reads the notes,
  does the work, and **appends a Handoff block** (below).
- **waddy** later scans notes files for new Handoff blocks and acts.

The Obsidian export (`tools/export_obsidian.py`) inlines `notes.md` read-only
into the vault, so Handoff blocks show up in the projected task note for human
review automatically — no extra step.

## The Handoff block (worker writes this)

Append to the **end** of `private/tasks/<task-id>/notes.md`. Append-only; never
edit or delete earlier blocks.

```markdown
## Handoff <ISO-8601-timestamp> — session <session-id>
- state: ready-to-close | blocked | in-progress
- did: <concise summary of what was accomplished>
- artifacts: <PR/issue refs and URLs, comma-separated, or "none">
- for-waddy: <the action requested of waddy>
```

Field rules:
- `state`:
  - `ready-to-close` — work is done; waddy should complete the task (verify the
    named artifacts first, e.g. a PR is merged / CI green).
  - `blocked` — work stopped on a dependency; `for-waddy` names the blocker.
  - `in-progress` — checkpoint; more work coming, just recording progress.
- `session-id` — the worker's own Copilot session id (from its runtime), so
  waddy can correlate and, if needed, read that session for detail.
- Keep it greppable: the heading must start with `## Handoff ` at column 0.

## Scanning + processing (waddy reads this)

1. Glob `private/tasks/*/notes.md`; grep for lines matching `^## Handoff `.
2. For each block, parse the timestamp, session-id, and fields.
3. **Dedupe**: a block is "new" if no `touches[]` entry on that task already
   records it. Record processed blocks as a touch:
   `{"at": <now>, "via": "handoff", "note": "handoff <ts> session <id>: <state> — <did>"}`
   and add the worker session-id to the task's `copilot_session_ids` if absent.
4. **Act on `state`:**
   - `ready-to-close` → verify artifacts, then run the `complete-task` flow
     (confirm with the user first per waddy's "propose, don't autopilot" rule).
   - `blocked` → set task `status` to `blocked`, surface the blocker to the user.
   - `in-progress` → update `last_touched_at`; no status change.
5. Never auto-merge/close public artifacts from a handoff without user
   confirmation.

## Optional: session ledger (deterministic, via hooks)

Handoff blocks are model-written (judgment). For the *mechanical* problem of
"which session touched what, when", a user-level **hook** appends lossless ledger
entries to a JSONL file (`private/session-ledger.jsonl`), independent of
session-store compaction:

- `sessionStart` / `sessionEnd` → `{event, session_id, cwd, repo, branch, ts}`.
- `userPromptSubmitted` → a **claim** entry `{event: "claim", task_id,
  session_id, cwd, repo, ts}` **only when** the prompt contains a
  `waddy-task:<id>` marker (as emitted by a `start-worker` brief). This binds
  task↔session **at pickup time — before any work — so it survives an interrupt
  or crash** even if the worker never writes a Handoff block.

To find which session picked up a task: grep the ledger for `"task_id": "<id>"`.
The ledger complements handoffs; it does not replace them (it has no notion of
task intent or outcome).
