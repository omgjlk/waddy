---
name: slack-saved-for-later
description: >
  Process Slack "Saved for later" items. Each saved item is a to-do-ish
  thing the user marked for follow-up. This skill lists them, dedupes
  against already-tracked tasks, and proposes start-task for each unresolved
  one. Read-only on Slack — never unsave or modify.
---

# slack-saved-for-later

Trigger phrases: "process my saved for later", "clean up saved slack",
"what did I save for later", "drain saved".

## Steps

1. **Fetch saved items** via `slack-mcp`:

   ```
   slack_search_public_and_private
     query="is:saved"
     sort=timestamp  sort_dir=asc  limit=20
     channel_types="public_channel,private_channel,im,mpim"
   ```

   Paginate with `cursor` until exhausted (cap at 100 items to avoid
   overwhelming the user; if more, note the count and ask to continue).

2. **Dedupe against active state.** For each saved item, check if its
   permalink matches any `tasks[*].links[*]` in `private/state.json`. If
   so, mark as "already tracked, skip".

3. **For each remaining item, classify:**

   - **Actionable** — needs me to do something (review, reply, decide,
     write).
   - **Reference** — info worth keeping but no action.
   - **Stale** — older than 30 days and unactioned; likely safe to skip.

4. **Propose actions.** Present a numbered list:

   ```
   📌 Saved for later — 7 items (5 actionable, 1 reference, 1 stale)

   Actionable:
     1. #eng-team — @alice asks "should we deprecate X?" (3d ago)
        → start-task "Decide on deprecation of X", kind=investigation
     2. PR github/foo#123 — review requested by @bob (1d ago)
        → start-task "Review github/foo#123", kind=pr-review
     ...

   Reference:
     6. Link to design doc in #architecture
        → note-only, append to private/slack/saved-reference.md

   Stale (45d): 1 item — skip?

   Pick which to proceed with: all / 1,3,5 / skip
   ```

5. **Execute the user's selection.** For each chosen item, invoke
   `start-task` with the parsed dump (URL + summary). For reference items,
   append to `private/slack/saved-reference.md`. Never modify the saved
   state in Slack.

6. **Append a record** to `private/slack/<YYYY-MM-DD>-saved-drain.md` so
   we have an audit trail of what we processed.

## Hard rules

- **NEVER** call Slack write tools (none should exist in this config).
- **NEVER** mark items unsaved — that's the user's decision in the Slack
  UI.
- Slack content stays in `private/` only.
