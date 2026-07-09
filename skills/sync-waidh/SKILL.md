---
name: sync-waidh
description: >
  Reconcile the waddy state with the WAIDH GitHub Projects board and the user's
  assigned GitHub issues. Read-mostly drift check: ensures public tasks are on
  the board with the mapped status, surfaces assigned issues not tracked, and
  flags status mismatches and stale draft/artifact swaps. Never closes issues or
  hand-moves issue/PR cards to Done (automation owns Done). Meant to run inside
  morning-brief / daily-summary, or on demand ("sync my board", "reconcile WAIDH").
---

# sync-waidh

Read `_lib/board.md` and `_lib/state.md` first. This is the periodic drift check
that keeps the WAIDH board honest without letting it silently diverge from
reality. It is **propose-don't-autopilot** for anything destructive.

Trigger phrases: "sync my board", "reconcile WAIDH", "is my board up to date?",
"audit my tasks vs the board". Also called by `morning-brief` and
`daily-summary`.

## Inputs (three sources)

1. **waddy state** — `private/state.json` (`active_tasks`, `paused_tasks`,
   `recent_completed`, each task's `visibility`, `status`, `board_item_id`,
   `issue`/`pr`).
2. **WAIDH board** — `projects_list` method `list_project_items` (pass
   `fields:[board.status_field_id]`), from `private/config.json → board`.
3. **Assigned issues** — `search_issues` `assignee:<user.login> is:open` scoped
   to the repos/orgs that matter (see config `tracking_repo` + known work orgs).

## What it does automatically (safe, non-destructive)

- **Project public tasks onto the board.** For each `active`/`paused` task with
  `visibility: public` and no `board_item_id`: add its issue/PR (preferred) or a
  draft, cache `board_item_id`, and set the mapped Status (see `_lib/board.md`
  status map). This is the same write `start-task` would have done.
- **Align status for on-board tasks.** If a task's waddy `status` maps to a
  different board Status than the card currently shows, update the card —
  **except** never hand-set Done on an issue/PR-backed card (automation owns
  that; if the artifact is closed but the card isn't Done, surface it instead).
- **Cache missing linkage.** If a task is on the board but `board_item_id` isn't
  stored in state, backfill it.

## What it only SURFACES (never auto-acts)

Present these as a short triage list for the user to action:

1. **Assigned issues not on the board** — candidate inbox. Group by likely
   action (real work -> add; noise like on-call logs / hardware alerts ->
   unassign/close) but **do not** close or unassign without explicit per-issue
   confirmation.
2. **Closed artifact, card not Done** — either the board workflow isn't enabled
   (remind the user of the 3 toggles in `_lib/board.md`) or it's a draft needing
   a manual Done.
3. **Status mismatch** — waddy says `done` but card is In progress, or vice
   versa; waddy `paused` but card In progress; etc.
4. **Draft with a real artifact now** — a draft card whose work gained an
   issue/PR -> propose a **swap** (add artifact, copy status, delete draft).
5. **Board item with no waddy task** — informational only. GitHub is the source
   of truth for these; do **not** force-create a waddy task.

## Guardrails

- **Never close a GitHub issue/PR.** That is always an explicit, per-issue user
  decision.
- **Never hand-move an issue/PR card to Done.** Enable/rely on the board's
  "closed -> Done" workflow (`_lib/board.md`).
- **Never put a `private` task on the board.**
- **Never call `updateProjectV2Field`** (see the hard rule at the top of
  `_lib/board.md`).
- All board field IDs / option IDs come from `private/config.json` — never
  hard-code them.

## Output

A compact report:
```
WAIDH sync — <N> public tasks on board, <M> aligned this run
Surfaced:
  - <k> assigned issues not tracked  (...refs...)
  - <k> cards whose artifact is closed but not Done
  - <k> status mismatches
  - <k> drafts with a real artifact to swap
```
Then offer to action the surfaced items (with confirmation).
