---
name: meeting-prep
description: >
  Prepare for an upcoming meeting. Pulls meeting details from Outlook
  via workiq, fetches linked documents/PRs, cross-references active
  tasks, and produces a 30-second briefing with talking points and
  pre-read recommendations.
---

# meeting-prep

Trigger phrases: "prep my next meeting", "prep for <meeting name>",
"what's coming up", "get me ready for <X>".

## Inputs

Optional meeting identifier:
- "next" / "next meeting" (default)
- A meeting subject keyword (e.g., "architecture review")
- An exact title or organizer name

## Steps

1. **Find the meeting.** Use workiq:

   ```
   workiq-ask_work_iq
     question="What is my next meeting (or the meeting matching '<X>')?
              Give me: subject, start time, duration, organizer,
              attendee list, location/teams link, agenda, and links to
              attached documents."
   ```

2. **Resolve linked artifacts.** From the workiq response:
   - For each attached SharePoint/OneDrive doc URL, optionally pass it
     back to workiq with `fileUrls: [<url>]` to summarize.
   - For any GitHub URLs in the agenda, use `github-mcp-server` to fetch
     the issue/PR title, status, and recent comments.

3. **Cross-reference state.** For each attendee, see if the user has any
   `tasks[*]` referencing their work (search task titles, links, notes).
   For the meeting subject, fuzzy-match against `tasks[*].title`.

4. **Slack context (optional, lightweight).** Search for messages
   between the user and the organizer or the topic in the last 7 days
   to surface recent thinking. Counts + brief excerpts only.

5. **Compose a 30-second brief:**

   ```
   📋 Prep — <subject> @ <start> (<duration>, <attendee-count> attendees)

   👥 Attendees: <list>
   🎯 Goal (from agenda): <one line>

   📎 Pre-read:
     • <doc-title> — <2-line summary>
     • PR github/foo#123 — <status, what changed since last view>

   🔗 Related active task: <title> (task <id>) — last touched <when>

   💬 Talking points:
     • <inferred from agenda + recent slack/docs>
     • <…>

   ❓ Open questions to surface:
     • <…>
   ```

6. **Cache the brief.** Save to
   `private/meetings/<YYYY-MM-DD>-<slug>-prep.md` so it's available
   during the meeting and for later reference.

7. **Offer to start a task.** Ask:

   > "Track this meeting as a task (e.g., to capture follow-ups)? (yes/no)"

   On yes, invoke `start-task` with kind `meeting-followup`, linked to
   the prep doc.

## Hard rules

- Meeting content stays in `private/`. Never commit a prep doc.
- If workiq EULA not accepted, halt politely with a setup pointer.
