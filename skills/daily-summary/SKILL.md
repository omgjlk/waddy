---
name: daily-summary
description: >
  Produce a shareable end-of-day summary of what @omgjlk did today. Pulls
  from `private/state.json` (touches, transitions), GitHub activity
  (commits, PRs, comments via github-mcp-server), and high-level Slack
  participation (counts only, no content). Output is a short markdown
  block suitable for posting in a status channel.
---

# daily-summary

Trigger phrases: "daily summary", "end of day", "wrap up the day",
"what did I do today", "EOD".

## Inputs

Optional `date` (default: today). Optional `audience`:
- `slack` (default) — terse, emoji-friendly, no internal task IDs
- `internal` — verbose, includes task IDs and timestamps

## Steps

1. **Read** `private/state.json` and `private/config.json`.

2. **Touches today.** Walk `tasks[*].touches[*]` where `at` is within
   the requested date (user's local TZ from `private/config.json`
   if set, else system TZ). Group by task. For each task, list:
   - The transitions (start, switch, pause, resume, complete).
   - Any free-text notes from `touch-task` calls.

3. **GitHub activity today.** For each task with `issue` or `pr`:

   - Use `github-mcp-server-list_commits` since `<today-00:00>` with
     `author=<user.login>` to gather commits.
   - Use `github-mcp-server-search_issues` / `search_pull_requests`
     with `author:<login> updated:<today>` for cross-repo activity not
     already attached to a task.

4. **Completions today.** From `recent_completed` where `completed_at`
   is today, pull title + outcome.

5. **Slack signal (counts only).** Use `slack_search_public_and_private`
   with `from:<@me> after:<today>` to count messages sent by the user.
   DO NOT include the content. Just a count.

6. **Compose.**

   `audience=slack`:

   ```
   📊 @omgjlk — <date>

   ✅ Shipped:
     • <title> — <outcome>

   🟢 Progress:
     • <title> — <one-line summary of touches>
     • <title> — <one-line>

   📝 Open:
     • <title> (focus, <N> hrs)
     • <title> (paused)

   ⌨️  <X> commits across <Y> repos · <Z> PR comments · <W> Slack messages
   ```

   `audience=internal` adds task IDs, board item URLs, and per-touch
   timestamps. Save this version to
   `private/summaries/<YYYY-MM-DD>.md` for the user's record.

7. **Offer**: ask if the user wants the Slack version copied to clipboard
   (`pbcopy` on macOS):

   > "Copy slack version to clipboard? (yes/no)"

## Hard rules

- The slack-audience version MUST NOT include real-name attribution,
  internal codenames, or anything that would violate the sanitization
  rule applied at the GitHub level. (The summary will be pasted into
  Slack which is internal, but the summary should still be safe to share
  widely within the company.)
- **Never** include the *content* of Slack messages — counts only.
- Internal version saved to `private/summaries/` (gitignored).
