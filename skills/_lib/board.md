# Board interaction conventions

The waddy project board is a GitHub Projects (v2) board. All interaction goes
through `github-mcp-server` (see [tool preference memo for @omgjlk]).
Configuration lives in `private/config.json`.

## ⚠️ NEVER call `updateProjectV2Field` to modify status options

GraphQL's `updateProjectV2Field` mutation **replaces** the entire
`singleSelectOptions` array, even when you pass back every existing
option with the same names. GitHub assigns each option a brand-new
`optionId`, which orphans every existing item whose status pointed at
the old ids — they all collapse to "No Status" in the UI. On a board
with hundreds of Done items this is silently catastrophic; the
restoration requires fetching every item, mapping by option *name*, and
re-applying the status via `updateProjectV2ItemFieldValue` one at a
time. There is no rollback.

**Add or rename status options manually via the project Settings UI**
(Project page → ··· → Settings → Status field → Add option). Then
read the new option ids back with the github-mcp-server
`list_project_fields` call and store them in `private/config.json` →
`board.status_options`.

This rule applies any time you need to change *any* single-select field
on the board, not just Status.

## Reading `private/config.json`

```json
{
  "board": {
    "owner": "<org-or-user-login>",
    "owner_type": "org",
    "project_number": <your-project-number>,
    "status_field_id": "PVTSSF_...",
    "status_options": {
      "todo":        "<option-id>",
      "in_progress": "<option-id>",
      "paused":      "<option-id>",
      "done":        "<option-id>"
    }
  },
  "user":           { "login": "<github-handle>" },
  "tracking_repo":  "<owner>/<repo>"
}
```

## Tools used

| Action | Tool | Notes |
| --- | --- | --- |
| Inspect project | `github-mcp-server-projects_get` (method `get_project`) | Sanity-check before any write |
| List items | `github-mcp-server-projects_list` (method `list_project_items`) | Pass `fields: [status_field_id]` to see status |
| Add issue/PR to board | `github-mcp-server-projects_write` (method `add_project_item`) | `item_type: "issue"` or `"pull_request"` |
| Update status | `github-mcp-server-projects_write` (method `update_project_item`) | `updated_field: {id: status_field_id, value: {single_select_option_id: "..."}}` |
| Remove item | `github-mcp-server-projects_write` (method `delete_project_item`) | Rare — usually move to Done instead |

## Draft items (board entries with no backing issue/PR)

`github-mcp-server` does **not** currently expose a method to create a
*draft* project item (one without an underlying issue or PR). Two workarounds:

1. **Preferred**: create a tracking issue in `<tracking_repo>` (from config),
   then add it to the board. This gives the entry a permalink and a place
   for richer notes.
2. **Fallback**: shell out to `gh api graphql` with the
   `addProjectV2DraftIssue` mutation. Only do this if the user explicitly
   asks for a draft (no issue).

GraphQL fallback shape (use sparingly):

```bash
gh api graphql -f query='
mutation($projectId: ID!, $title: String!, $body: String!) {
  addProjectV2DraftIssue(input: {projectId: $projectId, title: $title, body: $body}) {
    projectItem { id }
  }
}' -F projectId="$PROJECT_NODE_ID" -F title="..." -F body="..."
```

The `PROJECT_NODE_ID` is the `node_id` from `projects_get` (e.g. `PVT_...`),
NOT the numeric project number. Cache it in `private/config.json` under
`board.node_id` on first use.

## Status transitions

The four status values correspond 1:1 to task-state transitions:

| Task event | Board status |
| --- | --- |
| `start-task` creates new | **In progress** |
| `pause-task` | **Paused** |
| `resume-task` | **In progress** |
| `complete-task` | **Done** |
| `switch-to` / `touch-task` | (no change — focus is private) |
| Board entry created without intent to start now | **To do** (rare) |

Always resolve the option ID via `status_options[...]` in config, never
hard-code an ID in repo files.

## Updating an item's status

```json
{
  "method": "update_project_item",
  "owner": "<board.owner>",
  "owner_type": "<board.owner_type>",
  "project_number": <board.project_number>,
  "item_id": <numeric item id>,
  "updated_field": {
    "id": <board.status_field_database_id as number>,
    "value": "<board.status_options.in_progress as string>"
  }
}
```

Notes:

- `updated_field.id` is the **numeric** field database id
  (`status_field_database_id` in config), not the `PVTSSF_...` node id.
- `updated_field.value` for a single-select field is the **bare option id
  string** (e.g. `"<option-id>"`), NOT a wrapped object like
  `{single_select_option_id: "..."}`. The MCP server rejects the wrapped
  form with a 422.
- `item_id` for `update_project_item` is the numeric `databaseId` returned
  inside the project-item object — **not** the `PVTI_...` `node_id`.

## Getting the numeric item id after `add_project_item`

`add_project_item` only returns the `node_id` (string `PVTI_...`). To get
the numeric `id` needed for subsequent `update_project_item` calls, follow
up with a `list_project_items` filtered query:

```
method:        list_project_items
owner:         <board.owner>
owner_type:    <board.owner_type>
project_number:<board.project_number>
query:         "repo:<owner>/<repo>"     # or a more specific filter
fields:        ["<board.status_field_database_id>"]
```

The response includes `id` (numeric) and `node_id` (string) for each item.
Cache both in `private/state.json` as `board_item_number` and `board_item_id`
respectively.

## Status map (waddy status → board Status option)

The board's Status single-select has four options (ids in `config.json →
board.status_options`). Map waddy task `status` values onto them:

| waddy `status` | board Status | option key |
| --- | --- | --- |
| (just added, not started) | To do | `todo` |
| `in_progress`, `active`, `root-caused`, `handed-off`, `waiting_review` | In progress | `in_progress` |
| `paused` | Paused | `paused` |
| `done` | Done | `done` |

"In progress" is the catch-all for *any* live work — investigations, reviews,
handed-off items awaiting a worker, etc. Only use Paused for genuinely
set-aside work, and Done for closed-out work.

## Visibility: what belongs on the board

Each task carries a `visibility` field (`public` | `private`). **Only `public`
tasks are projected to the WAIDH board** — it's a shared surface others read.

Default heuristic when `start-task` doesn't get an explicit value:
- **`public`** — has a GitHub artifact (`issue`/`pr`), or `kind` is
  `incident`/`initiative`/`epic`/`outreach`/`pitch`/`adr`/`pr-review`, or the
  work produces something others consume (docs, presentations).
- **`private`** — personal tooling (e.g. waddy/Obsidian), one-off triage/routing,
  private investigations, access recovery, reading/prep tasks.

When unsure, ask the user once at `start-task`. Never move a `private` task onto
the board.

## Automation owns the "Done" column — do NOT hand-move issue/PR cards to Done

**Status: workflows CONFIRMED ENABLED on board 15464 as of 2026-07-09** — the
"Item closed → Done" and "PR merged → Done" workflows are live, so closing/merging
the backing artifact moves its card to Done automatically.

Enable GitHub Projects' built-in **Workflows** on the board (Project → ··· →
Settings → Workflows) so closure is handled by GitHub, not by waddy:

1. **Item closed → Set Status: Done**
2. **Pull request merged → Set Status: Done**
3. (optional) **Auto-archive items** after N days in Done, to keep the open
   views clean.

Consequences for skills:
- `complete-task` **must not** set Status→Done for a card that has a backing
  **issue or PR** — closing the artifact will trigger the workflow. Setting it
  manually races the automation and hides the real closure signal. Just update
  state and let GitHub move the column when the artifact closes.
- **Drafts have nothing to close**, so `complete-task` *does* set drafts to Done
  manually (see below).

## Prefer a real tracking issue over a draft

A draft card can't participate in the "closed → Done" automation and has no
permalink for others. So whenever `public` work *could* have an issue:
- **Preferred:** create/there-exists a tracking issue (in `tracking_repo` or the
  relevant repo) and add **that** to the board.
- **Draft only** when the work legitimately has no home issue (e.g. a Slack-only
  incident being handed to another team) — and expect to move it to Done by hand.

When a draft later gains a real artifact, **swap** it (add the issue/PR, copy any
status, delete the draft) rather than leaving a duplicate.

## Lifecycle side-effects (board writes happen as a side-effect of the waddy verbs)

| waddy verb | board effect |
| --- | --- |
| `start-task` (visibility `public`) | ensure a card exists (issue/PR preferred, else draft) → Status **In progress** (start-task = actively starting); store `board_item_id` (+ `board_item_number`) and `issue`/`pr` on the task |
| `start-task` (visibility `private`) | no board write |
| reconcile / triage-add (not being worked yet) | add card → Status **To do** |
| `switch-to` (focus target on board, currently **To do**) | promote that one card **To do → In progress**; no other board change |
| `pause-task` | set card **Paused** |
| `resume-task` | set card **In progress** |
| `complete-task`, card backed by issue/PR | **no board write** — close the artifact; the workflow moves it to Done |
| `complete-task`, draft card | set card **Done** manually |

## Reconcile (`sync-waidh`) — run at morning-brief / daily-summary

A periodic drift check (this is the audit codified). For each `public` task,
ensure it's on the board with the mapped status and, if it has an artifact, that
the **artifact** (not a stale draft) is the card. Then surface, without
auto-fixing destructive things:
- assigned open issues (in relevant repos) **not** on the board → triage inbox;
- board items whose backing issue/PR is closed but card isn't Done (automation
  gap / draft) ;
- status mismatches between state.json and the board (e.g. waddy `done` but card
  still In progress);
- Done drafts that now have a real artifact to swap.
Board items with **no** waddy task are fine — GitHub is the source of truth for
those; don't force-create waddy tasks for them.
