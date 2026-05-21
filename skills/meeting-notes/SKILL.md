---
name: meeting-notes
description: >
  Turn a Teams meeting transcript (via workiq) into a durable,
  Obsidian-friendly markdown note. Structures into Decisions, Action
  items (with owners + dates), Open questions, and condensed Discussion.
  Links action items to existing tasks or proposes start-task for new
  ones. Writes to `private/notes/` (Obsidian stub) until the user wires
  up an Obsidian vault path.
---

# meeting-notes

Trigger phrases: "notes from my meeting", "transcribe <X>",
"process the transcript", "meeting notes for <subject>".

## Inputs

Meeting identifier:
- "last meeting" / "today's <subject>" / "the standup"
- An exact subject keyword
- A specific meeting time/title

## Steps

1. **Locate the transcript.** Use workiq:

   ```
   workiq-ask_work_iq
     question="Find the transcript of my most recent (or specified)
              meeting: <X>. Return: subject, start time, attendees, and
              the full transcript text."
   ```

   If no transcript is available, tell the user (transcripts aren't
   generated for every meeting) and offer to capture manual notes
   instead.

2. **Run the action-item-extractor plugin skill** with the transcript
   text as input. This is one of the WorkIQ-provided skills already
   installed; it returns a structured list of action items with owner,
   priority, and deadline guesses.

3. **Parse the transcript into four buckets** (in your own pass, using
   the LLM):
   - **Decisions** — explicit "we decided to X" / "agreed to Y" lines.
   - **Action items** — merge action-item-extractor output with anything
     you spot.
   - **Open questions** — unresolved or punted items.
   - **Discussion** — a condensed narrative (NOT verbatim — aim for 5–10
     bullet points covering the substance).

4. **Cross-reference tasks.** For each action item:
   - If owner is @omgjlk: cross-ref against active `tasks[*]`. If
     match → propose `touch-task` with the action item as the note. If
     no match → propose `start-task`.
   - If owner is someone else: just record it; no waddy task is created
     for other people's work.

5. **Render the note** using `templates/meeting-note.md` with these
   fields:
   - `title` — meeting subject
   - `date` — meeting date (YYYY-MM-DD)
   - `attendees` — full list
   - `linked_tasks` — task IDs that this meeting touches

6. **Write to disk:**

   - If `private/config.json` has `obsidian.vault_path` set and the
     directory exists: write to `<vault>/Inbox/<YYYY-MM-DD>-<slug>.md`.
   - Otherwise (current default): write to
     `private/notes/<YYYY-MM-DD>-<slug>.md`.

   The path is the same Obsidian-compatible markdown either way — moving
   the file later is just `mv`.

7. **Reply:**

   ```
   📝 Notes saved → <path>
      <X> decisions, <Y> action items (<Z> mine), <W> open questions

   Proposed waddy actions:
     • touch task <id> "<title>" (action item: <one line>)
     • start-task "<title>", kind=meeting-followup (action item: <one line>)
     • <…>

   Approve all / pick / skip?
   ```

## Hard rules

- Transcripts contain real names and may contain confidential matters.
  They live in `private/notes/` (or the user's Obsidian vault, which is
  outside this repo). NEVER copy any transcript or note content into a
  tracked file.
- Verbatim quotes are OK *inside the note* (still in `private/`), but
  the public-facing version (if the user ever asks for one) MUST be
  redacted manually.
