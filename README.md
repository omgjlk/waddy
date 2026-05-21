# waddy — What Am I Doing Here?

A personal [Copilot CLI](https://docs.github.com/copilot/how-tos/use-copilot-agents/use-copilot-cli) agent that helps me (and maybe you) track what I'm actually spending my days doing.

I shipped this repo publicly so others can fork it, gut the personal bits, and adapt it. Nothing here references my actual work — all of that lives in a gitignored `private/` directory on my laptop. The only thing committed is the generic agent definition, skills, and templates.

## What it does

- Accepts a free-form "I'm starting on X" dump (with optional links) and turns it into:
  - A tracking issue or PR link (when relevant)
  - An entry on a GitHub Project (v2) board with status **To do / In progress / Paused / Done**
  - A durable internal note in `private/tasks/<task-id>/`
- Models concurrent work natively. I have ADHD and routinely have several things in flight at once — `start-task` **never** auto-pauses anything. Switching focus is cheap (`switch-to`); pausing is an explicit, deliberate action.
- Reviews Slack output a few times a day and proposes tracking entries for significant time-sinks or notable threads — without marking anything read.
- Reads Outlook calendar (via [WorkIQ](https://github.com/microsoft/work-iq)) for morning briefings and meeting prep.
- Turns Teams meeting transcripts into durable, Obsidian-friendly notes.
- Peeks at running Copilot CLI sessions to figure out what I've actually been doing when I forget to tell it.
- Produces a shareable end-of-day summary and a "what should I be doing today" morning brief.

## What it does NOT do

- Auto-mark Slack messages as read.
- Post to your project board on your behalf without confirmation on the first run of a new skill.
- Commit anything that lives under `private/` — gitignore is enforced.

## Requirements

- [GitHub Copilot CLI](https://docs.github.com/copilot/how-tos/set-up/install-copilot-cli)
- MCP servers:
  - `github-mcp-server` (preconfigured by Copilot CLI)
  - [`slack-mcp`](https://github.com/github/copilot-slack-mcp) (Slack reading)
  - [`workiq`](https://github.com/microsoft/work-iq) (Outlook / Teams / Office)
- A GitHub Project (v2) board with a single-select `Status` field including options `To do`, `In progress`, `Paused`, `Done`. Add `Paused` via the project's field settings if it isn't present.

## Setup (for forkers)

1. Clone this repo to wherever you keep your tools.
2. Copy `private/config.example.json` to `private/config.json` and fill in your board info:
   ```json
   {
     "board": {
       "owner": "your-org-or-user",
       "owner_type": "org",
       "project_number": 12345,
       "status_field_id": "PVTSSF_...",
       "status_options": {
         "todo": "...",
         "in_progress": "...",
         "paused": "...",
         "done": "..."
       }
     },
     "user": { "login": "your-github-handle" },
     "tracking_repo": "your-github-handle/waddy"
   }
   ```
3. Initialize `private/state.json`:
   ```json
   { "active_tasks": [], "focus": null, "paused_tasks": [], "recent_completed": [], "tasks": {} }
   ```
4. Open Copilot CLI in this directory. The repo-level custom agent in `.github/agents/waddy.md` will load automatically.
5. Try `waddy, start a task: experimenting with waddy`.

## Repository layout

| Path | What it is |
| --- | --- |
| `.github/agents/` | Custom agent profiles loaded by Copilot CLI |
| `skills/` | Composable skill instructions (each is a `SKILL.md`) |
| `skills/_lib/` | Shared conventions referenced by multiple skills |
| `templates/` | Generic body templates for issues and board cards |
| `private/` *(gitignored)* | All real-work state, raw captures, durable notes |

## Inspiration / credit

Built collaboratively with Copilot CLI itself. The design intentionally favors **observability over autopilot** — waddy mostly *proposes* and asks; the human stays in the loop on what gets committed to memory and the board.

## License

MIT — see [LICENSE](./LICENSE).
