---
name: writing-style
description: >
  Apply Google developer documentation style to anything waddy writes for
  humans: issue and PR titles and bodies, comments, board items, Slack
  messages, meeting notes, and status reports. Runs implicitly before any
  write to a public surface, and explicitly when the user asks for a style
  pass on a draft.
---

# writing-style

Trigger phrases: "style check this", "run the style guide over this",
"rewrite this in Google style", "does this follow the style guide",
"clean up this draft", "edit this before I post it".

This skill also runs **implicitly**. Any time you're about to create an
issue, open a PR, post a comment, write a board item, send a Slack
message, or produce a meeting note or status report, apply
`skills/_lib/writing-style.md` to the draft before you show it to the
user. No trigger phrase required.

## Steps

1. Read `skills/_lib/writing-style.md`. It's the canonical rule set —
   don't work from memory.

2. Identify the surface: issue, PR, comment, board item, Slack message,
   meeting note, status report, or tracked repo file. Surface-specific
   rules override the general ones. In particular:
   - PR bodies stay terse. A few sentences plus a small table.
   - Slack tolerates a slightly warmer register than a document does.
   - Word and docx output uses bare full URLs so they autolink.

3. Draft or revise the content against the rules, in this order:
   1. **Structure.** Sentence-case title with no trailing period. Lead
      with what this is and why it matters. Condition before
      instruction. Headings only if the length warrants them.
   2. **Voice.** Active voice with a named actor. Present tense. Second
      person for instructions.
   3. **Word choice.** Remove _please_, _simply_, _just_, _easily_,
      _obviously_, _e.g._, _i.e._, _etc._, _leverage_, and exclamation
      points. Replace ableist, gendered, violent, and figurative
      language with the precise term.
   4. **Formatting.** Code font for identifiers, paths, commands, and
      literals. Bold only for UI elements and run-in headings.
      Parallel list items introduced by a complete sentence.
   5. **Links.** Descriptive text over a fully-qualified URL. Never
      `#1234` or `org/repo#1234`. Never "click here" or "this issue".
   6. **Numbers and dates.** Spell out zero through nine, numerals for
      10 and up, numerals always for versions and technical quantities.
      `January 19, 2026` or ISO `2026-01-19`. `3 PM`, not `3:00pm`.

4. Run the pre-publish checklist at the end of
   `skills/_lib/writing-style.md`.

5. Show the user the rendered draft **before** writing it anywhere. For
   an explicit style-pass request, also list what you changed and why,
   grouped by rule — for example, "removed three instances of _simply_",
   "converted two shorthand issue refs to full URLs". Keep the
   explanation to a handful of lines.

6. Write only after the user approves.

## Judgment calls

Google's guide is guidance, not law, and it says so. Depart from it when
the result is clearly better, and stay consistent within the document.
Common cases where departing is right:

- An established term in the reader's domain beats the style guide's
  preferred spelling.
- A code sample, log line, or quoted message stays verbatim. Never edit
  quoted text for style.
- Terseness beats thoroughness in a PR body, every time.

When a style rule and a user instruction conflict, the user wins. When
two style rules conflict, prefer the one that makes the text clearer to
someone skimming it in a hurry.

## What this skill MUST NOT do

- Rewrite quoted material, transcripts, log output, code, commit
  messages already written by others, or anything the user pasted and
  asked you to preserve verbatim.
- Expand a PR body in the name of completeness.
- Rewrite the user's own words in a Slack draft without saying what you
  changed.
- Post, comment, or commit anything before the user approves the
  rendered draft.
- Apply document style to conversational CLI replies. Talk to the user
  normally.
