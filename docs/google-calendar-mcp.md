# Google Calendar MCP — wiring guide

The waddy agent reads work calendar data via `workiq` (Outlook). For
personal calendar conflict checks, the
[`@cocal/google-calendar-mcp`](https://github.com/nspady/google-calendar-mcp)
server is used.

## Least-privilege design

The upstream server hard-codes the broad
`https://www.googleapis.com/auth/calendar` OAuth scope (read + write +
delete) and does not expose a way to narrow it via environment variable.
Rather than fork-and-patch, waddy constrains what the agent can actually
do at the **MCP tool filter** layer in the Copilot CLI MCP config
(`.mcp.json` at the repo root, or `~/.copilot/mcp-config.json`). The
token Google issued is broadly scoped; the allowlist is what limits it.

**Currently permitted:** all read tools, plus `create-event` and
`update-event`.

**Deliberately withheld:** `delete-event`, `respond-to-event`, and
`manage-accounts` — the agent literally cannot invoke them.

The reasoning: `create-event` without `update-event` is a trap, because
the agent could create a wrong event and be unable to correct it. But a
bad **delete** on a personal calendar is not recoverable agent-side, and
RSVPs are visible to other people, so both stay off. `manage-accounts`
is not needed for any waddy workflow.

If you want a true read-only token (defense in depth at Google's API),
clone the upstream repo, change the scope in `build/auth-server.js` to
`.../auth/calendar.readonly`, and point the MCP command at your local
build instead of `npx`. Note this forecloses event creation entirely.

## Setup steps

1. **Create a Google Cloud project** and enable the Calendar API:
   https://console.cloud.google.com/apis/library/calendar-json.googleapis.com.
2. **Configure the OAuth consent screen.** If your account is a Google
   Workspace account, choose **Internal** — no test-user dance and no
   weekly token expiration. Plain `@gmail.com` accounts must use
   **External** + add themselves as a test user.
3. **Generate an OAuth client** (Application type: **Desktop app**) and
   download the JSON.
4. **Store it outside the repo:**

   ```bash
   mkdir -p ~/.config/google-calendar-mcp
   mv ~/Downloads/client_secret_*.json ~/.config/google-calendar-mcp/credentials.json
   chmod 600 ~/.config/google-calendar-mcp/credentials.json
   ```

5. **Add to a Copilot CLI MCP config.** Two options:

   **Option A — Workspace-scoped (recommended for waddy).** The MCP
   server only loads when Copilot CLI's cwd is this repo. Avoids
   spawning the npx subprocess for every Copilot session everywhere
   on your machine. Create `.mcp.json` at the waddy repo root (already
   gitignored):

   ```json
   {
     "mcpServers": {
       "google-calendar": {
         "type": "local",
         "command": "npx",
         "args": ["-y", "@cocal/google-calendar-mcp"],
         "env": {
           "GOOGLE_OAUTH_CREDENTIALS": "/Users/<you>/.config/google-calendar-mcp/credentials.json"
         },
         "tools": [
           "list-calendars",
           "list-events",
           "get-event",
           "search-events",
           "get-freebusy",
           "get-current-time",
           "list-colors"
         ]
       }
     }
   }
   ```

   See `.mcp.json.example` at the repo root for a copy-paste template.

   **Option B — User-global.** Same JSON shape, placed in
   `~/.copilot/mcp-config.json` (merged into the existing `mcpServers`
   object). The server then loads for every Copilot CLI session,
   regardless of cwd. Use this only if you want personal-calendar
   reads from outside the waddy repo.

   Either way, the `tools` array is the allowlist that bounds what the
   agent can do. It currently permits the read tools plus
   `create-event` and `update-event`. Adding `delete-event`,
   `respond-to-event`, or `manage-accounts` grants irreversible or
   externally-visible actions on a personal calendar — do not add them
   unless you know what you're doing.

6. **Trigger first-run OAuth consent** from the terminal:

   ```bash
   GOOGLE_OAUTH_CREDENTIALS=~/.config/google-calendar-mcp/credentials.json \
     npx -y @cocal/google-calendar-mcp auth
   ```

   A browser tab opens; approve. The refresh token is saved to
   `~/.config/google-calendar-mcp/tokens.json`. Lock it down:

   ```bash
   chmod 600 ~/.config/google-calendar-mcp/tokens.json
   ```

7. **Flip the waddy config flag.** In `private/config.json`:

   ```json
   "google_calendar": {
     "enabled": true,
     "calendar_id": "primary",
     "credentials_path": "~/.config/google-calendar-mcp/credentials.json"
   }
   ```

8. **Smoke test.** Ask the agent "list my Google calendars" — it should
   return the calendar list.

## Once wired

The `morning-brief` skill will:

- Pull today's events from both Outlook (workiq) and Google Calendar.
- Flag overlaps and back-to-backs as conflicts.
- Surface personal events with subject only (no description) —
  privacy-by-default.

The `meeting-prep` skill stays Outlook-only by default; pass
`--include-personal` (or say "include personal calendar") to widen the
scope.

## What waddy does NOT do

- Delete Google Calendar events, RSVP to invitations, or manage
  accounts — `delete-event`, `respond-to-event`, and `manage-accounts`
  are withheld via the MCP tool filter. Event **creation** and
  **edits** are permitted.
- Cache calendar data in tracked files.
- Read calendar contents older than the current day's lookback window
  unless you ask.

## Token expiration

- **Workspace Internal app**: tokens refresh indefinitely.
- **External app in test mode**: tokens expire after 7 days. Re-run the
  `auth` command from step 6 to refresh, or publish the app (Cloud
  Console → OAuth consent screen → **Publish**) to eliminate the
  expiry. Google will warn that the app is unverified — that's fine for
  personal use.

