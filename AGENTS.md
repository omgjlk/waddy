# AGENTS.md — guidance for any agent working in the waddy repo

This file is loaded by Copilot CLI (and other agentic tools that respect the
[AGENTS.md convention](https://docs.github.com/copilot/how-tos/copilot-cli/add-custom-instructions))
whenever the cwd is the `waddy` repo.

## What this repo is

A personal "What Am I Doing Here?" agent definition. The repo is **public and
generic**. The real, sensitive operational state — current tasks, slack
snippets, meeting transcripts, real task titles — lives in a gitignored
`private/` directory.

## Hard rules

1. **Never commit anything under `private/`.** The `.gitignore` enforces this,
   but you should also never read content from `private/` and copy it into
   a tracked file. If a tracked file needs configuration that varies per user,
   document the shape and have the user put their values in `private/config.json`.
2. **The committed repo must stay generic.** No internal codenames, customer
   names, real issue refs, real org-only URLs, or anything that would
   embarrass the owner if it were on the front page of Hacker News.
3. **Never auto-pause a task on `start-task`.** The user multitasks. Multiple
   "In progress" board items at once is normal.
4. **Never mark Slack messages as read.** Use read-only Slack MCP methods only.
5. **Use the right MCP for the job:**
   - GitHub (issues, PRs, projects, repos) → `github-mcp-server`
   - Slack (channels, DMs, threads, saved-for-later) → `slack-mcp`
   - Outlook / Teams / Office / Word docs → `workiq`
   - Personal Google Calendar → (deferred)
6. **Propose, don't autopilot.** For anything that writes to a public surface
   (issues, PRs, board items, Slack), confirm with the user the first time
   in a session unless they've explicitly said "just do it".

## Where things live

- Primary agent profile: `.github/agents/waddy.md`
- Subagents: `.github/agents/{slack-reviewer,calendar-briefer,meeting-notetaker}.md`
- Skills: `skills/<name>/SKILL.md`
- Shared conventions: `skills/_lib/{board,sanitization,state}.md`
- Templates: `templates/`
- Optional integration guides: `docs/`
- Runtime state (gitignored): `private/state.json`, `private/config.json`,
  `private/tasks/`, `private/slack/`, `private/meetings/`,
  `private/notes/`, `private/summaries/`
- Scratch space (gitignored): `private/scratch/` — use this for any
  ephemeral file work (intermediate jq pipelines, draft outputs,
  one-off prompts). **Do not write to `/tmp` or other paths outside
  the repo tree** — keeping scratch under `private/` makes permissions
  simpler and ensures nothing accidentally leaks into a tracked commit.

## State file schema

See `skills/_lib/state.md`. The short version:

```json
{
  "active_tasks": ["task-id", "..."],
  "focus": "task-id or null",
  "paused_tasks": ["task-id", "..."],
  "recent_completed": [{"id": "...", "title": "...", "completed_at": "..."}],
  "tasks": { "task-id": { /* see state.md */ } }
}
```

`active_tasks` is a **set**, not a stack. The `focus` pointer is a soft hint
about where attention is right now; it changes cheaply via `switch-to` and
does not move tasks between board columns.

## Task IDs

Use `YYYY-MM-DD-<slug>` where `<slug>` is a short kebab-case description
generated from the dump. Example: `2026-05-21-bootstrap-waddy`.

## When in doubt

Ask the user. waddy is an ADHD-friendly tool, which means assumptions about
"the obvious next step" are usually wrong. Surface ambiguity early.
