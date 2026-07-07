---
name: handoff
description: >
  Cross-session work handoff. Two directions: (1) a WORKER session appends a
  structured Handoff block to a task's notes file to report what it did and what
  waddy should do next; (2) waddy SCANS task notes for new Handoff blocks, folds
  them into state.json, and acts (close / unblock / note). Lets sessions
  coordinate through files instead of introspecting each other's transcripts.
---

# handoff

Read `_lib/handoff.md` first — it defines the channel, the Handoff block format,
and the scan/parse rules. This skill is the operational wrapper around it.

Trigger phrases:
- Worker side: "hand this back to waddy", "write a handoff", "I'm done with the
  handed-off task", "record a handoff for <task>".
- waddy side: "process handoffs", "any handoffs?", "check for handoffs",
  "catch up on worker sessions". Also run opportunistically during
  `morning-brief` and `resume-task`.

## Mode A — write a handoff (worker session)

Use when the current session was handed a waddy task and is done, blocked, or
checkpointing.

1. Determine the task's notes path. It was provided when the work was handed off
   (e.g. `~/src/waddy/private/tasks/<task-id>/notes.md`). If unknown, ask the
   user for the task-id or notes path — do not guess.
2. Get this session's own session-id from the runtime.
3. Append a Handoff block (format in `_lib/handoff.md`) to the **end** of the
   notes file. Append-only — never modify earlier content.
   - Fill `state`, `did`, `artifacts` (real PR/issue refs), `for-waddy`.
   - Be specific in `artifacts`: waddy verifies these before closing.
4. Confirm to the user what was written and where.

This mode only writes one file; it needs no board/state access and works from
any repo.

## Mode B — process handoffs (waddy)

1. **Load context.** Read `private/config.json` and `private/state.json`
   (see `_lib/state.md`). Read `_lib/handoff.md` if not in context.
2. **Scan.** Glob `private/tasks/*/notes.md`, grep `^## Handoff `. Collect
   blocks; parse timestamp, session-id, `state`, `did`, `artifacts`, `for-waddy`.
3. **Filter to new blocks.** Skip any already recorded in that task's
   `touches[]` (dedupe on `<ts> session <id>`).
4. **For each new handoff**, per `_lib/handoff.md`:
   - Add a `touches[]` entry (`via: "handoff"`); add the worker session-id to
     `copilot_session_ids` if absent.
   - `ready-to-close` → verify the named artifacts (e.g. PR merged, CI green via
     `github-mcp-server`). If verified, **propose** completing the task
     (`complete-task`); confirm with the user first. If not verified, report the
     gap and leave the task open.
   - `blocked` → set `status: "blocked"`; surface the blocker (`for-waddy`).
   - `in-progress` → bump `last_touched_at`; summarize progress. No status change.
5. **Summarize** to the user: per task, what the handoff said and the action you
   took or propose.
6. **Refresh the projection** (optional): if the Obsidian export is in use, run
   `python3 tools/export_obsidian.py` so the vault reflects the new state.

## Guardrails

- Respect "propose, don't autopilot": never auto-close a task or merge/close a
  public artifact from a handoff without user confirmation.
- Handoffs are authoritative for *intent*, not for *artifact state* — always
  verify PRs/issues named in `artifacts` before acting on `ready-to-close`.
- Keep blocks append-only; the notes file is a shared log, not a scratchpad to
  rewrite.

## Handing work off (waddy → worker)

When waddy sets a task up for another session (see `start-task`), give the
worker three things so it can use Mode A:
1. The task-id and its notes path (`internal_notes_path`).
2. A one-line contract: "When done/blocked, append a `## Handoff` block to that
   file per waddy's handoff convention."
3. Any relevant links (issue/PR/board).
A dedicated `start-worker` helper can automate this later.
