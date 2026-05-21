---
name: start-task
description: >
  Create a new task from a free-form dump (text, links, optionally references
  to an existing issue/PR). Adds the task to `active_tasks`, sets it as the
  current `focus`, creates a board entry on the WAIDH project in "In progress"
  status (and a tracking issue if one isn't supplied). DOES NOT pause any
  other active tasks — multi-active is the norm.
---

# start-task

Trigger phrases: "start a task", "start tracking", "I'm working on …",
"add to the board: …", "begin: …".

## Input

A free-form blob from the user. May include:
- A short title or description
- One or more URLs (issue, PR, doc, slack thread)
- A `#owner/repo#NN` or `#NN` reference (Copilot CLI's `#` mention)
- A `kind` hint (e.g. "PR review", "doc review", "investigation")

## Steps

1. **Load context.**
   - Read `private/config.json` (halt with a setup prompt if missing — see
     `_lib/state.md` "first-run bootstrap").
   - Read `private/state.json` (initialize if missing).
   - Read `_lib/board.md` and `_lib/state.md` if not already in context.

2. **Parse the dump.**
   - Extract title (first ~80 chars, or use a smart summary if the dump is
     long).
   - Extract URLs. Classify each as: github-issue, github-pr, github-other,
     slack, docs, other.
   - Infer `kind`:
     - PR URL → `pr-review`
     - Issue URL → `issue`
     - Word/Docs URL → `doc-review`
     - Slack URL → `slack-thread`
     - Else: ask the user, defaulting to `investigation` or `other`.
   - Generate `task-id` = `YYYY-MM-DD-<slug>` (today's date, kebab-case slug
     from title, 2–4 words). If collision, suffix `-2`, `-3`.

3. **Determine backing artifact.** In order:
   a. If the dump contains an issue URL or `#owner/repo#NN`: use that issue.
   b. Else if it contains a PR URL: use that PR (kind = `pr-review`).
   c. Else: ask:

      > "No issue or PR was referenced. Should I (1) create a tracking
      > issue in `<tracking_repo>`, (2) create a draft board item with no
      > backing issue, or (3) just track this internally without a board
      > entry?"

      Default recommendation: (1) create a tracking issue. Draft items are
      possible but less linkable.

4. **Create the tracking issue (if path 3a).**
   - Use `github-mcp-server` `create_issue` on `<tracking_repo>` from
     `private/config.json`.
   - Title = task title.
   - Body = render `templates/tracking-issue.md` with: links, kind, today's
     date, and a "Tracked by waddy" footer.
   - Capture the issue number.

5. **Add to the board.**
   - For issue/PR-backed tasks: `projects_write` method `add_project_item`
     with `item_type` = "issue"|"pull_request" and the appropriate
     `issue_number`|`pull_request_number`, `item_owner`, `item_repo` from
     parsed URL or `tracking_repo`.
   - Capture the returned item `id` (numeric) and `node_id` (string).
   - For draft items (path 3b): use the GraphQL fallback documented in
     `_lib/board.md`.

6. **Set status to "In progress".**
   - `projects_write` method `update_project_item`:
     ```
     updated_field: { id: <board.status_field_id>, value: { single_select_option_id: <board.status_options.in_progress> } }
     ```

7. **Mutate `private/state.json`.**
   - Add a `tasks["<task-id>"]` entry per the schema in `_lib/state.md`:
     `status: "in_progress"`, `started_at` & `last_touched_at` = now,
     `kind`, `links`, `board_item_id`, `board_item_number`, `issue`/`pr`
     fields, `touches: [{at: now, via: "start"}]`,
     `internal_notes_path: "private/tasks/<task-id>/notes.md"`.
   - Append `<task-id>` to `active_tasks` (idempotent set).
   - Set `focus = "<task-id>"`.
   - **Do not touch any other task's status or board column.**

8. **Create the internal notes file.**
   - Write `private/tasks/<task-id>/notes.md` with the raw dump verbatim
     under a "## Initial dump" heading. This is where waddy and the user
     will accumulate internal-only context that should never reach the
     public surface.

9. **Confirm to the user.**

   Reply with a 3-line summary:
   ```
   ✅ Started task: <title>
      Board: <board item URL>
      Internal notes: private/tasks/<task-id>/notes.md
   ```

   If there are other active tasks, append a one-liner:
   ```
   ℹ️  3 other tasks remain active (focus is on the new one).
       Run `waddy status` to see them all.
   ```

## What this skill MUST NOT do

- Move any other task to Paused.
- Auto-mark anything in Slack.
- Commit any file outside `private/`.
- Hard-code field IDs (always resolve from `private/config.json`).

## Error handling

- If `github-mcp-server` returns an error on `add_project_item` (e.g. the
  issue is already on the board), gracefully fetch the existing item ID via
  `list_project_items` query and proceed with the status update.
- If `update_project_item` fails after the item is added, leave a clear
  message and continue — the state file is still authoritative and the
  user can fix the column manually.
