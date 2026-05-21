---
name: status
description: >
  Show the current state of work: active tasks (with focus highlighted),
  paused tasks, and the last few completed. Read-only. The "what am I
  doing right now?" query.
---

# status

Trigger phrases: "status", "what am I doing", "what's on my plate",
"show me the board", "where am I".

## Steps

1. Read `private/state.json`.
2. Format a concise report:

   ```
   🎯 Focus: <title> (task <task-id>) — last touched <relative time>

   🟢 In progress (<N>):
      • <title> (<task-id>) — <kind> — <links if any>
      • <title> (<task-id>) — …
      …

   ⏸  Paused (<N>):
      • <title> (<task-id>) — <since when paused>

   ✅ Recently completed (last <min(N,5)>):
      • <title> (<completed_at relative>)
      …
   ```

3. If `private/state.json` is empty or doesn't exist, reply:
   ```
   No tasks tracked yet. Try: "waddy, start a task: <description>".
   ```

## What this skill MUST NOT do

- Hit the board API. The local state is canonical for the report; rely on
  it. (A future `status --sync` flag could reconcile; not in scope here.)
- Modify any state.
