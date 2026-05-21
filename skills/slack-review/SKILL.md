---
name: slack-review
description: >
  Read-only review of recent Slack activity (mentions, DMs, threads @omgjlk
  participated in) since the last review. Surfaces clusters of significant
  time spent or notable discussion outcomes and proposes one of:
  touch an existing task, create a new tracking issue/start-task, write a
  durable raw note, or ignore. NEVER marks anything as read; NEVER sends
  messages. Use a few times a day.
---

# slack-review

Trigger phrases: "review my slack", "catch me up on slack",
"what happened in slack", "scan slack".

## Inputs

Optional `since` argument:
- Absolute (`2026-05-21T08:00`)
- Relative (`4h`, `yesterday`, `since-last-review`)
- Default: read `private/slack/last-review.json` → `at`; if missing, use
  `now() - 4h`.

## State files (all gitignored)

- `private/slack/last-review.json` — `{"at": "<ISO-8601>"}`
- `private/slack/<YYYY-MM-DD>-review.md` — durable raw notes from this review
  (appended if the same date is reviewed twice)

## Steps

1. **Load context.** Read `private/state.json` (for active/paused task
   titles and links), `private/config.json` (for user info), and the
   `last-review.json` (or use the override from input).

2. **Pull three buckets in parallel** via `slack-mcp` tools. The current
   user's Slack id is `<U...>` (from `slack_search_users` self lookup —
   cache it in `private/slack/me.json` on first run).

   a. **Mentions of me** since `since`:
      ```
      slack_search_public_and_private
        query="to:me after:<YYYY-MM-DD>"
        sort=timestamp  sort_dir=asc  limit=20
      ```
      (Combine with `slack_search_public` results too if the user has many
      public-channel mentions; the public variant doesn't require consent.)

   b. **DMs to/from me** since `since`:
      ```
      slack_search_public_and_private
        query="in:<@me> after:<YYYY-MM-DD>"
        channel_types="im,mpim"
        sort=timestamp  sort_dir=asc  limit=20
      ```

   c. **Threads I participated in** since `since`:
      ```
      slack_search_public_and_private
        query="from:<@me> is:thread after:<YYYY-MM-DD>"
        sort=timestamp  sort_dir=asc  limit=20
      ```

3. **Group results into clusters.** A cluster is one of:
   - A thread (group all messages with the same `thread_ts`).
   - A 1:1 DM channel within a 30-minute window.
   - A topic match across channels (LLM-judged loosely).

4. **For each cluster, classify:**
   - **Significant** — >5 messages, OR a decision/commitment, OR a
     question awaiting @omgjlk's response, OR cross-team coordination.
   - **Noise** — emoji reactions, single-line acks, status bot pings.

   Drop noise; carry significant clusters forward.

5. **For each significant cluster, propose one of:**

   - **Touch an existing task.** If a thread URL, GitHub link, or topic
     matches an active task in `state.json`, invoke the `touch-task` skill
     with `via: "slack-review"` and a short note.
   - **Start a new task.** If the cluster represents new work or an
     ongoing-but-untracked effort, invoke `start-task` with a draft dump
     (suggest a kind based on content).
   - **Note only.** If it's just context worth remembering but not actively
     tracked work, append to `private/slack/<YYYY-MM-DD>-review.md`.
   - **Ignore.** Mention briefly so the user knows you considered it.

   **Always propose, don't auto-execute** unless the user has explicitly
   said "just do it" or "autopilot" earlier in the session.

6. **Update `private/slack/last-review.json`** to `now()`.

7. **Reply** with a concise summary:

   ```
   📥 Slack review — <since> → now (<duration>)

   🔥 Significant (3):
     1. Thread in #engineering about "X" (5 msgs, decision)
        → Proposal: touch task <id> "<title>"
     2. DM from @jane about "Y" (open question)
        → Proposal: start-task "<title>", kind=investigation
     3. Cluster in #project-z (8 msgs, lots of links)
        → Proposal: note-only, saved to private/slack/2026-05-21-review.md

   🪶 Noise dropped: 47 messages

   Proceed with all proposals? (yes / pick / skip)
   ```

## Hard rules

- **NEVER** call any Slack tool that would mark a message read or send a
  message. The `slack-mcp` server in this setup is read-only by config;
  if a write tool ever appears, do not use it.
- **NEVER** copy verbatim Slack content into a tracked file under
  `omgjlk/waddy`. Slack content is private — it goes only in `private/`.
- The DM/private-channel search requires user consent per
  `use-slack-mcp` skill conventions. If the user hasn't given consent in
  this session, ask:
  > "OK to search DMs and private channels for this review? (yes/no)"
  Default to public-channel-only on `no`.
