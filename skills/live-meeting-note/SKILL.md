---
name: live-meeting-note
description: >
  Prepare an empty, structured meeting note in the user's Obsidian vault
  and open it in Obsidian so the user can write notes live DURING a
  meeting. Distinct from `meeting-prep` (a pre-meeting research brief)
  and `meeting-notes` (post-meeting transcript processing). This is the
  real-time capture surface: a scaffolded note, opened and ready to type
  into.
---

# live-meeting-note

Trigger phrases: "open a note for my 1:1", "prep a place for notes and
open obsidian", "give me a note to write in during <meeting>", "open an
obsidian note for <X>", "note for my meeting with <person>".

Use this when the user wants to **take notes live**, not when they want a
research brief (`meeting-prep`) or a transcript write-up afterward
(`meeting-notes`).

## Prerequisites: resolve the Obsidian vault

The note MUST live **inside** a registered Obsidian vault — Obsidian can
only open files that are within a vault, and the `obsidian://` URI keys
off the vault name.

1. Read `private/config.json` -> `obsidian.vault_path` and
   `obsidian.vault_name`.
2. If `vault_path` is `null`/missing, discover it:
   - macOS registered vaults live in
     `~/Library/Application Support/obsidian/obsidian.json` under
     `vaults` (each has a `path`). The vault **name** is the basename of
     that path.
   - Confirm the chosen vault with the user, then **persist** both
     `vault_path` and `vault_name` into `private/config.json` so this is
     a one-time discovery (mutate config via read -> write; it's
     gitignored).
3. If Obsidian isn't installed / no vault exists, fall back to writing
   the note to `private/meetings/` and tell the user it can't be opened
   in Obsidian.

## Steps

1. **Identify the meeting.** From the user's phrasing, or resolve the
   current/next meeting:
   - Work calendar (Outlook) via `workiq` (`/me/calendarView`), or
   - `google-calendar` for personal-calendar meetings.
   Capture: subject, date, attendees, organizer. If ambiguous, ask.

2. **Build the note path.**
   - Slug: kebab-case of the subject (e.g. `Jesse / Ying 1:1` ->
     `ying-1-1`; strip the user's own name from 1:1s for brevity).
   - Path: `<vault_path>/meetings/<YYYY-MM-DD>-<slug>.md`
     (create the `meetings/` folder if missing).
   - The vault-relative path (for the URI) is
     `meetings/<YYYY-MM-DD>-<slug>`.

3. **Render the note** from `templates/meeting-note.md`, filling
   `title`, `date`, `attendees`, and `tasks` (task IDs relevant to this
   meeting — fuzzy-match `tasks[*]` on subject/attendee).
   Add a short **"threads I could raise"** section seeded from the
   user's recently-touched active tasks (last ~5 by `last_touched`), so
   they have talking points one glance away. Keep it to one line each.

4. **Write the note** to the vault path (use `bash` heredoc / `create` —
   note that `edit`/`create` tool calls have occasionally hit permission
   timeouts; `bash` `cat > file << 'EOF'` is a reliable fallback).

5. **Open it in Obsidian** via the URI (URL-encode the `/` in the path
   as `%2F`):

   ```bash
   open "obsidian://open?vault=<vault_name>&file=meetings%2F<YYYY-MM-DD>-<slug>"
   ```

   `open` returning exit 0 means the URI was dispatched; Obsidian will
   focus the note (it must be inside the vault for this to land on the
   right file).

6. **Reply briefly** — confirm the note path is open in Obsidian and
   that the user can write live. Offer to process it afterward with
   `meeting-notes` (or fold in a transcript) once the meeting ends.

## Notes / gotchas (discovered, keep here so we don't rediscover)

- **Vault is canonical.** Meeting notes live **only** in the Obsidian
  vault (`<vault_path>/meetings/`) — one copy, no duplicates. Do **not**
  write a second copy to `private/meetings/`. `state.json` `links[]` for
  a meeting should point at the vault file (absolute path). The
  `private/meetings/` fallback is used **only** when Obsidian/a vault is
  unavailable (see prerequisites); tell the user it can't be opened in
  Obsidian in that case.
- **`obsidian://` URI:** `obsidian://open?vault=<name>&file=<vault-rel-path-no-extension>`.
  The `file` is relative to the vault root, `/` encoded as `%2F`, no
  `.md` extension.
- **Vault name != path:** the URI needs the vault *name* (its registered
  label), which is the basename of `vault_path` unless the user named it
  differently in Obsidian.
- This skill only scaffolds + opens; the user does the writing. Don't
  auto-populate meeting content.

## Hard rules

- Meeting notes contain real names and possibly confidential/1:1 matters.
  They live in the user's Obsidian vault (outside this repo) or
  `private/`. NEVER copy note content into a tracked file, and never
  commit anything under `private/` or the vault.
- 1:1s with a manager are sensitive — scaffold structure only; do not
  infer or write speculative content about performance, people, or
  private topics.
