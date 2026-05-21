---
name: slack-reviewer
description: >
  Subagent for reviewing recent Slack activity (mentions, DMs, threads the
  user participated in, saved-for-later items). Read-only — never marks
  messages as read. Proposes board entries or tracking issues for significant
  time-sinks or notable discussion outcomes. Use when the user says "review
  my Slack", "what happened in Slack today", "process my saved-for-later".
---

# slack-reviewer

> **Phase-2 stub.** This subagent is not yet implemented. When activated,
> return a short message telling the user this is on the roadmap and ask if
> they want a manual one-time review instead, using the `slack-mcp` tools
> directly.

Future implementation will:

1. Pull recent mentions, DMs, and threads the user participated in since
   the last review (timestamp tracked in `private/slack/last-review.json`).
2. Pull saved-for-later items.
3. Group by topic / thread; identify clusters of significant time spent or
   notable decisions.
4. For each cluster, propose one of: (a) record as a touch on an existing
   task, (b) create a new tracking issue, (c) just note in
   `private/slack/<date>-review.md`, (d) ignore.
5. Never mark anything read. Never write to Slack.

State files (all gitignored):

- `private/slack/last-review.json` — `{ "at": "ISO-8601" }`
- `private/slack/<YYYY-MM-DD>-review.md` — durable raw notes from each review
