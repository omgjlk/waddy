# Board interaction conventions

The waddy project board is a GitHub Projects (v2) board. All interaction goes
through `github-mcp-server` (see [tool preference memo for @omgjlk]).
Configuration lives in `private/config.json`.

## Reading `private/config.json`

```json
{
  "board": {
    "owner": "<org-or-user-login>",
    "owner_type": "org",
    "project_number": 15464,
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
  string** (e.g. `"ecccd1b9"`), NOT a wrapped object like
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
