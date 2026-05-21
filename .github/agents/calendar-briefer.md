---
name: calendar-briefer
description: >
  Subagent for morning briefings and meeting prep. Reads the user's Outlook
  calendar via WorkIQ, cross-references ongoing tasks in `private/state.json`,
  surfaces what's coming up and what prep is needed. Future: also reads
  personal Google Calendar for conflicts. Use when the user says "morning
  brief", "what's on my calendar", "prep for my next meeting".
---

# calendar-briefer

> **Phase-2 stub.** This subagent is not yet implemented.

Future implementation will:

1. Use `workiq` to fetch the next N hours / today's / tomorrow's calendar.
2. For each meeting:
   - Resolve attendees and topics.
   - Cross-reference against `private/state.json` active tasks to find
     relevant ongoing work.
   - Surface linked documents (Word, OneNote, SharePoint) via workiq.
   - Recommend prep actions (review PR X, re-read doc Y, draft talking points).
3. Flag conflicts with personal calendar (once Google Cal MCP is wired).
4. Produce a concise text block the user can read in 30 seconds.

State files (gitignored): none required — read-through.
