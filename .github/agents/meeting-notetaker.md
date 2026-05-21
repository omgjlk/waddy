---
name: meeting-notetaker
description: >
  Subagent for turning Teams meeting transcripts into durable, Obsidian-friendly
  notes. Pulls transcripts via WorkIQ, structures them into decisions / action
  items / open questions / discussion, links to relevant tasks. Use when the
  user says "notes from this meeting", "transcribe the X sync", "process the
  transcript".
---

# meeting-notetaker

> **Phase-2 stub.** This subagent is not yet implemented.

Future implementation will:

1. Use `workiq` to fetch the transcript for a named/recent meeting.
2. Parse into:
   - **Decisions** — what was concluded
   - **Action items** — who owes what by when (use `templates/meeting-note.md`)
   - **Open questions** — unresolved items
   - **Discussion** — condensed narrative, not verbatim
3. Cross-reference against `private/state.json` to link mentioned tasks.
4. Write to `private/notes/<YYYY-MM-DD>-<slug>.md` using `templates/meeting-note.md`.
5. Propose action items as `start-task` candidates if any are owed by @omgjlk.

When the user wires up an Obsidian vault, the output path will be
configurable via `private/config.json` → `obsidian.vault_path`. Until then,
write to `private/notes/` (which is Obsidian-compatible markdown).
