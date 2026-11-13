---
name: toil-log
description: >
  Keep the weekly support-and-toil log current. Runs the `toil-log` workflow
  (from `.github/extensions/toil-log/`) to draft entries since the last
  capture, shows the draft, and on approval updates the current issue, rolls
  over to a new weekly issue, and advances the cursor.
---

# toil-log

Trigger phrases: "update my toil issue", "toil log", "capture my toil".

The workflow drafts; this skill publishes. All settings live in
`private/toil/state.json` (repo, Slack user ID, permalink base, title
template, categories, exclusions, `cursor`, `current_issue`, `history`).

## Steps

1. **Run the workflow.** Call `run_dynamic_workflow` with name `toil-log`
   and no args (the window is `cursor` to now). Pass `until` to stop
   earlier, for example at the end of a period.
2. **Show the draft.** Read the `draftPath` it returns and render both
   sections plus the dropped list. Point out anything the summary flags as
   uncertain.
3. **On approval, publish** (drafts before writes; never skip approval):
   - Add the "Additions" section to the current issue. Edit the issue body:
     merge each bullet under its category heading, and add a dated
     `**<start> to <end>**` block if the body uses dated blocks.
   - If today is on or after `current_issue.period_end`, roll over: create
     the next issue from `title_template` with `intro`, a "Previous period:"
     link, and the "Next issue" bullets, assigned to the user, issue type
     Task. Then ask before closing the old issue as completed.
4. **Update state.** Set `cursor` to the run's `proposedCursor`. On
   rollover, append the new issue to `history` and set `current_issue`.
   Edit `private/toil/state.json` with the edit tool.

## Rules

- Weekly periods run Wednesday to Wednesday (`period_days: 7`).
- Never post from inside the workflow. Never advance the cursor before the
  draft is published, so a declined draft gets picked up next run.
- Follow `skills/_lib/writing-style.md`; no live `@`-mentions.
