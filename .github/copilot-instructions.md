# Copilot instructions for the waddy repo

See [`AGENTS.md`](../AGENTS.md) at the repo root for the canonical guidance.
The rules there are the rules here.

A few Copilot-CLI–specific notes:

- The primary custom agent is defined in [`.github/agents/waddy.md`](./agents/waddy.md).
  Copilot CLI will auto-discover it when this repo is the cwd.
- Subagents (`slack-reviewer`, `calendar-briefer`, `meeting-notetaker`) live
  next to it and are referenced by the primary agent.
- Skills referenced by the agent live under `skills/`. They are **not**
  installed as plugins — the agent reads the relevant `SKILL.md` on demand.
- Required MCP servers: `github-mcp-server`, `slack-mcp`, `workiq`. If any
  are missing, the agent should tell the user and degrade gracefully rather
  than guess.
