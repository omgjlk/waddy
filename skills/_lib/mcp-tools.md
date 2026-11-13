# MCP tool names: connectors and local servers

Waddy reaches Slack and Work IQ through
[Copilot connectors](https://docs.github.com/en/copilot/concepts/customizations/copilot-connectors)
when they're connected, and through local MCP servers or plugins otherwise.
Skills and agents name tools by their **logical name**, such as `fetch` or
`slack_read_thread`. Resolve the logical name to the tool your session
actually exposes.

## Resolving a logical name

Connector tools carry a generated prefix,
`github-copilot-connector-<hash>-<tool>`. The hash identifies the
connection and can change when you reconnect, so never hard-code it.

1. Find the tool whose name ends with the logical name. Connector names are
   truncated to 18 characters, so match on the start of the logical name too.
2. Pick the server by its tool set. The Work IQ connector exposes `ask`,
   `fetch`, `create_entity`, and `search_paths`. The Slack connector exposes
   `slack_*` tools.
3. If no connector is present, use the local server's tool: `workiq-<tool>`
   or `slack-<tool>`.

If neither source exposes the tool, tell the user which connector to connect
in `/mcp`, and continue with the rest of the task.

Connector tools may take different parameters than the local server's tool
of the same name. Read the tool's schema before calling it; don't copy
parameters from an example written for the other source.

## Slack

### Truncated names

| Logical name | Connector tool suffix |
|---|---|
| `slack_search_public` | `slack_search_publi` |
| `slack_search_public_and_private` | `slack_search_publ2` |
| `slack_search_channels` | `slack_search_chann` |
| `slack_read_user_profile` | `slack_read_user_pr` |
| `slack_list_channels` | `slack_list_channel` |
| `slack_list_user_channels` | `slack_list_user_ch` |

### Reads

Call these freely:

- `slack_search_*`: public, public and private, channels, users, emoji
- `slack_read_*`: thread, channel, canvas, file, list, user profile
- `slack_list_channel`, `slack_list_user_ch`

`slack_search_public_and_private` covers DMs and private channels, so get the
user's consent before using it, per the `use-slack-mcp` skill.

### Writes: ask first, every time

Any Slack tool that changes something is a write: `slack_add_*`,
`slack_create_*`, `slack_update_*`, `slack_complete_*`, and
`slack_get_file_upl*`. Before **each** write call:

1. Show the user exactly what will happen, in the `ask_user` form message:
   the tool, the destination (channel, DM, thread, canvas, or list), and the
   full rendered content or change.
2. Get explicit approval of that specific write.
3. Make the call only after approval, and only as shown. If the user edits
   the draft, show the revised version again before writing.

This rule has no exceptions:

- "Just do it" or autopilot permission given earlier in a session does
  **not** cover Slack writes.
- Approval of one write doesn't carry over to the next one, even in the same
  thread or batch.
- Skills that run unattended, such as `slack-review`, `morning-brief`, and
  scheduled prompts, never write to Slack.
- Never mark messages as read.

## Work IQ

The Work IQ connector exposes the same tools as the `workiq` plugin. Follow
the plugin's `workiq` skill for usage, and `skills/_lib/workiq-notes.md` for
operational details. The skill's `workiq-<tool>` examples map to the
connector's `<tool>`. Semantic questions go to `ask`; older docs call it
`workiq-ask_work_iq`.
