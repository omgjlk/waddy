# Writing style

waddy writes in [Google developer documentation style](https://developers.google.com/style).
This file is the working summary. Consult it whenever you draft text that
another human will read.

## Scope

Apply this style to every surface waddy writes to:

- GitHub issue titles and bodies
- Pull request titles and bodies
- Issue and PR comments, review comments
- Project board item titles and notes
- Slack messages and thread replies
- Meeting notes, prep docs, and status reports
- Tracked files in this repo, including this one

It does **not** apply to conversational replies in the CLI, to
`private/state.json`, or to code and commands. Chat with the user however
the user likes.

## Reference hierarchy

Google's guide says project-specific style wins. For waddy, resolve
questions in this order:

1. The user's explicit instruction in the current session.
2. The waddy overrides in this file. See
   [waddy overrides](#waddy-overrides).
3. The [Google developer documentation style guide](https://developers.google.com/style).
4. Merriam-Webster and the Chicago Manual of Style.

Break any rule when following it makes the text worse. Be consistent
within a single document.

## Voice and tone

- Write like a knowledgeable colleague, not a press release and not a
  standup comedian. Conversational, friendly, respectful.
- Use second person (_you_) for instructions. Use first person plural
  sparingly and only when it's literally true.
- Use active voice. Name the actor. Passive voice is fine when the actor
  is irrelevant or when you're deliberately de-emphasizing who did it —
  "Over 50 conflicts were found" reads better than "You created over 50
  conflicts."
- Use present tense. Reserve _will_ for events that genuinely happen
  later.
- Contractions are fine and usually better.
- State the condition before the instruction, so a reader can skip what
  doesn't apply: "To retry the job, run …" not "Run … if you want to
  retry the job."
- Don't use _please_ in instructions.
- Don't use exclamation points.
- Don't claim something is _simple_, _easy_, _just_, _obvious_, or
  _quick_. If it were, nobody would need the sentence.

## Words and phrases to avoid

| Avoid | Use instead |
| --- | --- |
| e.g. | for example |
| i.e. | that is |
| etc. | finish the list, or write "and other …" |
| tl;dr, ymmv, RTFM | write the sentence out |
| please note, at this time, it should be noted | delete the phrase |
| leverage (as a verb), utilize | use |
| simply, just, easily, obviously, of course | delete the word |
| & as a conjunction | and |
| sanity check | check, validate, confirm |
| crazy, insane, dumb, blind to, cripple | baffling, unexpected, slows down — pick the precise word |
| dummy value | placeholder value |
| blacklist / whitelist | denylist / allowlist, or blocked / allowed |
| master / slave | primary / replica, or the upstream project's current term |
| hover over, hit (a button) | point to, click |
| hangs | stops responding |
| pets vs. cattle, and other metaphors | describe the actual behavior |
| let's do X | do X |
| root cause | underlying problem, contributing factor, or describe what happened |
| man-hours, mankind | person-hours, humanity |

Also avoid pop-culture references, sports metaphors, US-specific
idioms, and figurative language generally. Readers are global, and a lot
of this content gets skimmed by people in a hurry.

Keep established technical terms that have a precise meaning even when
they sound violent or odd — `kill`, `abort`, `execute`, `terminate` are
fine when they name an actual command or API.

## Structure and formatting

- **Headings**: sentence case. Capitalize the first word and proper nouns
  only. No trailing period. "Rollback plan", not "Rollback Plan".
- **Titles**: sentence case, same rule. This includes issue titles, PR
  titles, and board item titles.
- **Lists**: introduce with a complete sentence, usually ending in a
  colon. Keep items grammatically parallel. Use sentence case. Use a
  numbered list only when order matters. Don't create a one-item list.
- **Tables**: sentence case in every cell, heading, and caption.
- **Bold**: UI elements and run-in list headings only.
- **Italics**: introducing or defining a term, and light emphasis. Use
  `_underscores_` in Markdown so italics stay distinguishable from bold.
- **Code font**: filenames, paths, commands, flags, class and method
  names, HTTP status codes, environment variables, literal values, and
  console output. Use fenced blocks for anything multi-line, with a
  language tag.
- **Placeholders**: all caps in code font — `PROJECT_ID`,
  `TASK_ID`.
- Don't underline anything except links. Don't hand-style fonts or
  colors.

## Links and references

- Write descriptive link text. Never _click here_, _this issue_, _this
  document_, or a bare _link_.
- Put the important words at the front of the link text.
- Introduce a standalone cross-reference with "For more information about
  X, see …". Use _about_, not _on_. Use _see_, not _refer to_.
- Make it clear why you're sending the reader somewhere.
- Don't repeat the same link several times in one document.
- Say so when a link downloads a file or opens something unexpected.

### waddy overrides

Two places where waddy departs from Google's guidance, both deliberate:

1. **Always use fully-qualified GitHub URLs as the link target.** Never
   `#1234`, never `org/repo#1234`. Shorthand refs resolve against
   whatever repo the reader is standing in, which is usually the wrong
   one. Write
   `[the runner autoscaling bug](https://github.com/org/repo/issues/1234)`.
2. **In Word, docx, and plain-text surfaces, a bare URL is acceptable.**
   Google says don't use a URL as link text; that rule assumes a renderer
   that makes link text clickable. When the destination is a Word
   document or a plain-text field, write the full
   `https://github.com/...` URL so it autolinks.

On GitHub and Slack, prefer descriptive text wrapped around the full
URL. That satisfies both rules at once.

## Mentions

**Never write a live `@`-mention on GitHub unless the user explicitly
asks for one.** Write the handle in code font instead: `` `@octocat` ``.

An `@`-mention subscribes that person to the thread. They then receive a
notification for every subsequent update until they unsubscribe by hand.
Naming someone in a tracking comment, an evidence log, or a sign-off
table is a reference, not a request for their attention, and it should
not cost them a subscription.

This applies to issue and PR bodies, comments, review comments, board
items, and commit messages. It does not apply when the user asks you to
ping someone, or when the whole point of the comment is to ask a named
person for something.

Slack is different: a mention there is the normal way to address someone
in a thread, and Slack doesn't create a durable subscription from it.
Use judgment, and still prefer not to mention people who aren't being
asked for anything.

## Numbers, dates, and times

- Spell out zero through nine. Use numerals for 10 and up.
- Always use numerals for versions, technical quantities, measurements,
  percentages, prices, and step numbers — `version 3`, `6 queries per
  second`, `8 GB`, `40%`.
- Spell out ordinals: _first_, _second_, not _1st_, _2nd_.
- Write dates as `January 19, 2026`. When space is tight, `Mon, Jan 19,
  2026` is fine — abbreviate the whole date or none of it.
- For a numeric-only date, use ISO 8601: `2026-01-19`. Never
  `01/19/2026`.
- Times use the 12-hour clock with a space before a capitalized AM or PM:
  `3 PM`, `3:45 PM`. Drop `:00` from round hours.
- Avoid time zones unless the reader needs one. When you need one, spell
  out the region and add the UTC offset, such as
  `US and Canadian Pacific Standard Time (UTC-8)`.
- Avoid seasons. Say the month or the quarter.
- Ranges use a hyphen with no spaces: `2024-2026`, `5-10 minutes`.

Task IDs keep their `YYYY-MM-DD-<slug>` form. That's an identifier, not
prose.

## Abbreviations

- Spell out an unfamiliar abbreviation on first use, with the
  abbreviation in parentheses: _Border Gateway Protocol_ (_BGP_).
- Don't spell out abbreviations that are more familiar than their
  expansion: API, CLI, CPU, HTML, PDF, RAM, REST, SDK, URL, PR.
- Don't invent abbreviations to save a few characters.
- Don't use an abbreviation as a verb.

## Surface-specific notes

### Issues

- Title: sentence case, states the problem or the outcome, no trailing
  period. Prefer a specific noun phrase over a vague one.
- Body: lead with what's happening and why it matters. Put context
  before instructions. Use headings only when the body is long enough to
  need them.
- Link every referenced issue, PR, run, or dashboard with a full URL and
  descriptive text.

### Pull requests

- Title: sentence case, imperative or descriptive, no trailing period.
- **Keep the body terse.** A few sentences plus a small table if a table
  helps. No boilerplate "Testing" / "Caveats" / "Motivation" scaffolding
  unless the change genuinely needs it. Long PR bodies get skimmed and
  then ignored.
- Terseness beats completeness here. This overrides any instinct toward
  thorough documentation-style prose.

### Slack

- One idea per message. Lead with the ask or the conclusion.
- Threads over channel spam.
- Code font for identifiers still applies. Headings usually don't.
- The tone rules still apply. So does the no-exclamation-point rule,
  within reason — Slack tolerates a bit more warmth than a doc does.

### Meeting notes and status reports

- Sentence case headings, parallel list items, active voice.
- Attribute decisions to a person or a group, not to the passive void:
  "The platform team decided to defer the migration", not "It was
  decided to defer the migration."
- Distinguish what was verified from what was inferred. Don't assert
  what someone knew, assumed, or missed without evidence. If it's an
  inference, label it.

### Documents that ask readers for something

A capacity plan, a design proposal, an ADR in review — anything where
named people owe you an answer. These grow with each round of feedback,
and the ask gets buried under the reasoning unless you separate them
deliberately.

- **Lead with the ask, not the derivation.** Open with what you need and
  from whom. How you arrived at the number goes below, or inside a
  collapsed `<details>` block. A reader who owes you a decision shouldn't
  have to read your working to find their question.
- **Give each reviewer one place to look.** If confirming a single layer
  means visiting a table, a caveat, an exclusions list, and a question at
  the bottom, the document has failed no matter how good each piece is.
  State the proposal, its exclusions, and the question together, once.
- **Address each question to the team that owns the answer.** A team that
  owns a component doesn't necessarily own what runs on it, what it
  connects to, or what it costs. Asking the wrong team wastes a round trip
  and can produce a confident answer from someone outside their scope.
- **Put "why this number changed" in the commit message.** The document
  carries the number and the reasoning that currently supports it. How it
  got there belongs in version control.
- **Replace, don't append.** When an answer lands, rewrite the assumption
  it settles. Adding a note beside a stale assumption leaves the reader to
  work out which one is current.

## Pre-publish checklist

Run this before writing to any public surface:

1. Is the title sentence case with no trailing period?
2. Does the first sentence say what this is and why it matters?
3. Is every link descriptive text over a fully-qualified URL?
4. Are all GitHub handles in code font rather than live `@`-mentions,
   unless the user asked for a ping?
5. Any _please_, _simply_, _just_, _e.g._, _i.e._, or exclamation
   points left?
6. Any ableist, gendered, violent, or figurative language?
7. Are list items parallel and introduced by a complete sentence?
8. Are dates unambiguous and numbers formatted right?
9. For a PR body: can you cut a third of it and lose nothing?
10. For a document that asks readers for something: can a named reviewer
    find their question, the proposal, and its exclusions in one place —
    and is it addressed to the team that owns the answer?
