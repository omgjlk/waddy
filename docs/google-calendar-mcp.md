# Google Calendar MCP — wiring guide

The waddy agent reads work calendar data via `workiq` (Outlook). For
personal calendar conflict checks, a Google Calendar MCP server is
needed. As of this writing it is **not yet wired** for @omgjlk's setup —
this doc captures how to do it when you're ready.

## Recommended MCP server

The community Google Calendar MCP server, e.g.
[`@cocal/google-calendar-mcp`](https://github.com/nspady/google-calendar-mcp)
or any other read-capable Google Calendar MCP that supports:

- Listing events in a date range
- Reading event details (attendees, location, attached docs)
- (Optional) Free/busy lookups

A read-only setup is sufficient for waddy — no write tools are required.

## Setup steps

1. **Create a Google Cloud project** and enable the Calendar API.
2. **Generate an OAuth client** (Desktop / Installed App type) and
   download `credentials.json`.
3. **Store it outside the repo** — e.g.
   `~/.config/google-calendar-mcp/credentials.json`.
4. **Add to `~/.copilot/mcp-config.json`:**

   ```json
   {
     "mcpServers": {
       "github-mcp-server": { "type": "http", "url": "https://api.githubcopilot.com/mcp/x/all" },
       "google-calendar": {
         "type": "stdio",
         "command": "npx",
         "args": ["-y", "@cocal/google-calendar-mcp"],
         "env": {
           "GOOGLE_OAUTH_CREDENTIALS": "/Users/omgjlk/.config/google-calendar-mcp/credentials.json"
         }
       }
     }
   }
   ```

5. **First-run consent**: when Copilot CLI starts and the MCP launches,
   it will open a browser for OAuth consent. Approve read-only scopes.
6. **Flip the waddy config flag.** In `private/config.json`:

   ```json
   "google_calendar": {
     "enabled": true,
     "calendar_id": "primary"
   }
   ```

## Once wired

The `morning-brief` skill will:

- Pull today's events from both Outlook (workiq) and Google Calendar.
- Flag overlaps and back-to-backs as conflicts.
- Include "personal" events with subject only (no description) in the
  brief — privacy-by-default.

The `meeting-prep` skill stays Outlook-only by default; pass
`--include-personal` (or say "include personal calendar") to widen the
scope.

## What waddy does NOT do

- Write to Google Calendar (no event creation/edits).
- Cache calendar data in tracked files.
- Read calendar contents older than the current day's lookback window
  unless you ask.
