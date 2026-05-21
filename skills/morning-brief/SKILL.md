---
name: morning-brief
description: >
  "What should I be doing today?" briefing. Combines: today's Outlook
  calendar (via workiq), incomplete work from yesterday (from
  `private/state.json`), any active+paused tasks, and an opportunistic
  Slack mentions/DMs scan. Output is a concise, prioritized block the
  user can read in 30 seconds.
---

# morning-brief

Trigger phrases: "morning brief", "what should I do today",
"what's on my plate", "kick off my day", "good morning".

## Steps

1. **Read local state.** `private/state.json` and `private/config.json`.

2. **Calendar (Outlook via workiq).** Ask:

   ```
   workiq-ask_work_iq
     question="What meetings do I have today? List them with start time,
              duration, organizer, attendees, and a one-line subject for
              each. Include links to any attached documents."
   ```

   If `workiq-accept_eula` hasn't been completed, tell the user and stop
   the calendar portion (don't block the rest of the brief).

3. **Personal calendar (deferred).** If `private/config.json` has
   `google_calendar.enabled = true`, run the Google Cal MCP equivalent
   (see `docs/google-calendar-mcp.md`). Otherwise note "personal calendar
   not wired yet" in the output.

4. **Yesterday's incomplete work.** From `state.json`:
   - All `active_tasks` and `paused_tasks` (these are what's open).
   - Anything `tasks[*].last_touched_at` within the last 24h whose status
     isn't `done`.

5. **Slack catch-up (lightweight).** Use `slack_search_public_and_private`
   to look for:
   - DMs since the user's last activity in Slack (best-effort: use
     `to:me after:<yesterday>`).
   - @mentions since yesterday.

   Cap at 5 items per bucket. Don't drain — that's `slack-review`'s job.
   Just count and surface the most-recent / highest-priority.

6. **GitHub notifications catch-up (lightweight).** Hit
   `http://localhost:8383/api/notifications` if the local gh-notify
   server is up; otherwise skip with a one-line note. Surface only:
   - High-priority count (red flag if >0)
   - 1–2 most-recent High-priority titles

   Don't drain — that's `notifications-review`'s job. If the user has
   reviewed notifications today (per
   `private/notifications/last-review.json`), report only deltas since
   that review.

7. **Cross-reference**: for each meeting, suggest prep based on:
   - Matching `tasks[*].title` or `tasks[*].links[*]`.
   - Meeting attendee list ∩ recent Slack activity.

8. **Output**:

   ```
   ☀️ Good morning, @omgjlk — <date>, <day-of-week>

   📅 Today's calendar (4 meetings, 3h total):
     09:00–09:30  Standup (recurring)
     11:00–12:00  Project X sync — prep: review PR #456 (linked to task <id>)
     14:00–15:00  1:1 with manager
     16:30–17:00  Architecture review (transcript will be available)

   🟢 Open work (3 active, 2 paused):
     focus  • <title> — last touched 18h ago
            • <title> — last touched 2d ago (consider pausing?)
            • <title> — paused 4d ago

   📥 Slack since yesterday:
     • 3 new DMs (most recent from @jane in #project-z)
     • 7 @mentions
     • Run `waddy, review my slack` to triage

   📬 GitHub notifications:
     • 4 High-priority (most recent: review_requested on github/foo#123)
     • 12 Medium · 37 Low
     • Run `waddy, review my notifications` to triage

   💡 Suggested order:
     1. Standup at 9 — 5 min prep
     2. Prep for Project X sync (~30 min on PR #456)
     3. Continue focus task <title>
     4. End-of-day: `waddy, daily-summary`
   ```

## Hard rules

- **Never** auto-touch tasks based on calendar/Slack scan. Surface
  candidates; the user decides.
- **Never** include verbatim email/meeting/Slack content in tracked
  files. The brief itself is ephemeral output to the user, but if you
  cache anything, it goes in `private/`.
