---
name: notifications-review
description: >
  Triage GitHub Notifications. Pulls pre-classified notifications from
  the user's local gh-notify server, cross-references each against
  active tasks in `private/state.json`, and proposes one of: touch an
  existing task, start a new task, summarize for later, or note-only.
  NEVER marks notifications as read and NEVER unsubscribes — those are
  destructive actions the user makes in the gh-notify UI where they can
  see full context.
---

# notifications-review

Trigger phrases: "review my notifications", "what's in my inbox",
"any new notifications", "triage notifications", "process my GH inbox".

## Why this skill exists

@omgjlk works heavily from GitHub Notifications and built their own
local triage tool, `gh-notify`, to classify notifications by priority
and surface what actually needs attention. This skill is a thin layer on
top: it consumes gh-notify's already-classified output and ties each
significant notification into the waddy task model so notifications
become trackable work rather than ephemeral noise.

## Data source

Primary: `http://localhost:8383/api/notifications` (the local gh-notify
server). Returns `NotificationsResponse`:

```jsonc
{
  "notifications": [
    {
      "id": "...",
      "reason": "review_requested",       // assign, mention, review_requested, author, ...
      "unread": true,
      "updated_at": "...",
      "subject": { "title": "...", "url": "...", "type": "PullRequest" },
      "repository": { "full_name": "owner/repo" },
      "priority": 1,                       // 1=High, 2=Medium, 3=Low
      "priority_label": "High",
      "pr_data": { /* state, reviewers, etc. */ },
      "auto_unsub_suggested": false,
      "auto_mark_read_suggested": false
    }
  ],
  "user": "omgjlk",
  "auto_unsubbed": [...], "auto_marked_read": [...]   // gh-notify's auto-mode suggestions
}
```

Source code: `/Users/omgjlk/src/omgjlk-playground/gh-notify`. Disk cache
fallback: `~/.cache/gh-notify/cache.json` (only if the server isn't
running; the cache schema is internal to gh-notify so prefer the HTTP
endpoint).

Last-resort fallback: `gh api notifications --paginate` for raw
notifications without classification.

## State files (gitignored)

- `private/notifications/last-review.json` — `{"at": "<ISO-8601>"}`
- `private/notifications/<YYYY-MM-DD>-review.md` — durable per-day notes
  (appended if reviewed multiple times the same day)

## Steps

1. **Detect data source.** Try the HTTP endpoint first:

   ```bash
   curl -s --max-time 3 http://localhost:8383/api/notifications | jq '.notifications | length'
   ```

   - If the server responds with a positive count → use it.
   - If the server is unreachable: tell the user "gh-notify server
     doesn't seem to be running" and offer to either (a) start it
     (`cd ~/src/omgjlk-playground/gh-notify && ./gh-notify &`), or (b)
     read the disk cache, or (c) fall back to raw `gh api
     notifications`. Default to asking; don't auto-start a background
     process.

2. **Read** `private/state.json`, `private/config.json`, and
   `last-review.json`.

3. **Group by priority** (High / Medium / Low) and within each group by
   repository.

4. **Cross-reference each notification** against tasks:

   - Extract issue/PR ref from `subject.url` (REST URL: convert to
     `owner/repo#NN` form).
   - Match against `tasks[*].issue`, `tasks[*].pr`, and any
     `tasks[*].links[*]` containing that ref.
   - Mark each notification as `tracked` (matches a task), `orphan`
     (no match), or `dependabot-group` (gh-notify pre-groups these —
     defer to its grouping decision).

5. **Compose proposals**:

   For **High priority — tracked**:
     → propose `touch-task <task-id>` with
       `via: "notifications"` and note `"<reason>: <subject.title>"`.

   For **High priority — orphan & actionable** (reason in
   {assign, mention, review_requested, security_alert}):
     → propose `start-task` with:
       - kind = `pr-review` if `subject.type == "PullRequest"`, else `issue`
       - dump = subject.title + the html_url + brief from PR/issue data

   For **Medium priority**:
     → list count + 2–3 representative titles. Ask "want to triage these
       individually?". Don't propose start-tasks by default — medium-pri
       items are usually FYIs.

   For **Low priority**:
     → counts only. Mention if any are flagged for auto-unsub.

   For **Dependabot groups**:
     → display the group as a single line (e.g. "12 dependabot PRs
       across 4 repos"). Offer to start a single tracking task for the
       whole batch only if @omgjlk plans to dedicate time to them.

6. **Auto-mode suggestions from gh-notify** — surface verbatim but
   never click for the user:

   ```
   🪶 gh-notify suggests:
     • 3 team-review notifications auto-unsub safe (PR already approved)
     • 2 merged-PR notifications safe to auto-mark-read
       → handle these in the gh-notify UI when you have a moment
   ```

7. **Persist** `private/notifications/last-review.json` to `now()` and
   append a summary to `private/notifications/<YYYY-MM-DD>-review.md`.

8. **Reply** with a compact summary:

   ```
   📬 Notifications — <since> → now (<duration>)

   🔥 High (5):
     1. PR github/foo#123 (review_requested) — matches task <id> "<title>"
        → Proposal: touch-task <id>
     2. Issue github/bar#456 (mention) — orphan
        → Proposal: start-task "Triage github/bar#456", kind=issue
     ...

   📨 Medium (12): drill in?
   🪶 Low (37): 8 auto-unsub-safe, 4 auto-mark-read-safe (handle in gh-notify)

   Proceed with high-priority proposals? (yes / pick / skip)
   ```

## Hard rules

- **Never mark notifications as read.** gh-notify exposes
  `/api/mark-read` and `/api/bulk-mark-read`; waddy must not call them.
- **Never unsubscribe.** Same for `/api/unsubscribe` and
  `/api/bulk-unsubscribe`.
- **Never enable auto-mode** for the user. The "Auto Mode" toggle in
  gh-notify is an explicit human decision.
- Notification content (titles, bodies of referenced issues/PRs) is
  often safe to log but may contain internal-only info — keep it in
  `private/` only, per the standard sanitization rules.
- gh-notify suggestions surfaced to the user are advisory: include the
  count, but make clear the action happens in the gh-notify UI.

## Integration: morning-brief

The `morning-brief` skill includes a high-priority notifications count
sourced from the same endpoint. If `notifications-review` runs and
updates `last-review.json`, the morning-brief should respect that and
report only deltas since the last review.
