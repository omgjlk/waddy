---
name: inspect-sessions
description: >
  Peek at recent and currently-running Copilot CLI sessions by reading
  `~/.copilot/session-store.db` (local SQLite). Correlates session
  activity with active tasks in `private/state.json` to figure out what
  the user has been working on — useful when they jumped into a session
  without saying "waddy, start a task". Proposes `touch-task` or
  `start-task` for orphaned session work.
---

# inspect-sessions

Trigger phrases: "what were my copilot sessions doing", "inspect sessions",
"what have I been working on", "find orphaned work".

## Inputs

Optional `since` (default: last 24h). Optional `cwd_filter` to scope to
sessions in a specific directory.

## Local data source

`~/.copilot/session-store.db` is a SQLite database with these tables
(verified 2026-05-21):

- `sessions(id, cwd, repository, branch, summary, created_at, updated_at, host_type)`
- `turns(session_id, turn_index, user_message, assistant_response, timestamp)`
- `checkpoints(session_id, checkpoint_number, title, overview, ...)`
- `session_files(session_id, file_path, tool_name, turn_index)`
- `session_refs(session_id, ref_type, ref_value, turn_index)` — `ref_type`
  values include `pr`, `issue`, `commit`. **This is the best signal for
  linking sessions to GitHub artifacts.**

Query via the `sqlite3` CLI in a bash shell. Do NOT modify the database.

## Steps

1. **List recent sessions** since the cutoff:

   ```bash
   sqlite3 -readonly ~/.copilot/session-store.db -json "
     SELECT id, cwd, repository, branch, summary, updated_at
     FROM sessions
     WHERE updated_at >= datetime('now', '-1 day')
     ORDER BY updated_at DESC
     LIMIT 30;
   "
   ```

   Adjust the time window from `since`.

2. **For each session, gather context:**

   ```bash
   sqlite3 -readonly ~/.copilot/session-store.db -json "
     SELECT ref_type, ref_value FROM session_refs
     WHERE session_id = '<id>'
     ORDER BY turn_index;
   "
   ```

   And the latest checkpoint title/overview if any.

3. **Match against waddy state.** For each session:
   - Compare `session_refs.ref_value` (issues/PRs) to `tasks[*].issue`,
     `tasks[*].pr`.
   - Compare `sessions.cwd` and `sessions.repository` to task links.
   - Compare session summary against task titles (loose match OK).

   Classify each session as:
   - **Tracked** — matches an active or paused task.
   - **Untracked** — does substantial work but no matching task.
   - **Trivial** — short session (<3 turns), no commits/refs — likely a
     one-off question.

4. **Propose actions:**

   - For **tracked** sessions: propose `touch-task` with
     `via: "copilot-session"` and a note like
     `"Session <short-id> in <cwd>: <checkpoint title or first turn>"`.
     Also record the `session_id` in `tasks[<id>].copilot_session_ids`.
   - For **untracked** sessions that did substantive work: propose
     `start-task` with a dump assembled from the session's
     repository/cwd/checkpoint/refs.
   - **Trivial** sessions: list count only, no action.

5. **Reply:**

   ```
   🔍 Sessions in the last 24h: 12

   🔗 Tracked → existing tasks (5):
     • <session-short-id> in <repo> → task <id> "<title>"
     • …

   ❓ Untracked / substantive (3):
     • <session-short-id> in <repo> — checkpoint: "<title>"
       → Propose start-task "<inferred title>", kind=<inferred>
     • …

   🪶 Trivial (4): skipped

   Apply proposals? all / pick / skip
   ```

## Hard rules

- **Read-only.** Open the SQLite DB with `-readonly`. Never write.
- Sessions may contain real names, emails, and snippets of source code
  the user worked on — same `private/` rules apply if you cache any
  session content. The `inspect-sessions` skill should NOT copy session
  content into the public repo.
- Don't propose actions on sessions in cwds the user has explicitly
  excluded (future: `private/config.json` → `inspect_sessions.exclude_cwds`).
