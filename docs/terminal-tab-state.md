# Terminal tab state

`tools/copilot_tab_state.py` shows what a Copilot CLI session is doing in the
terminal's own chrome, so you can tell a session that needs you from one that's
just thinking.

| State | iTerm2 | Metalterm | Meaning |
| --- | --- | --- | --- |
| `working` | amber tab | title `working` | A turn is running. |
| `attention` | red tab | title `NEEDS YOU` | Blocked on your approval or input. |
| `idle` | blue tab | title `idle` | Turn finished, waiting for you. |

## Why it exists

Copilot's built-in OSC 9;4 progress indicator distinguishes "a turn is in
flight" from "no turn is in flight" and nothing else. A turn blocked on a
permission prompt is still in flight, so the spinner keeps spinning and a
blocked tab looks exactly like a busy one — which is the distinction you most
need when several sessions run at once.

Hooks give you the turn boundaries, but no hook fires for "blocked on
approval": the documented `notification` hook doesn't cover permission prompts
in practice. That signal exists only in the session event stream, so the script
spawns a small watcher that tails `events.jsonl` for `permission.requested` and
`ask_user` tool calls.

## Terminal support

The two supported terminals need different escape sequences, and neither
supports the other's:

| Terminal | Tab state | Notifications |
| --- | --- | --- |
| iTerm2 | tab color, OSC 6 (proprietary) | OSC 9 |
| Metalterm | tab title, OSC 0 | OSC 777 |

Notifications are in-band, so the terminal raises them itself. They're
attributed to the terminal, and clicking one switches to the tab that raised
it. Metalterm suppresses its own banner while it's frontmost; iTerm2 doesn't,
so the script handles that case.

Other terminals: the script exits cleanly and does nothing.

## Install

1. Point a hook config at the script. Create
   `~/.copilot/hooks/copilot-tab-state.json`, replacing the path with your
   clone:

   ```json
   {
     "version": 1,
     "hooks": {
       "sessionStart": [
         {
           "type": "command",
           "bash": "python3 /path/to/waddy/tools/copilot_tab_state.py start",
           "timeoutSec": 5
         }
       ],
       "userPromptSubmitted": [
         {
           "type": "command",
           "bash": "python3 /path/to/waddy/tools/copilot_tab_state.py working",
           "timeoutSec": 5
         }
       ],
       "agentStop": [
         {
           "type": "command",
           "bash": "python3 /path/to/waddy/tools/copilot_tab_state.py idle",
           "timeoutSec": 5
         }
       ],
       "sessionEnd": [
         {
           "type": "command",
           "bash": "python3 /path/to/waddy/tools/copilot_tab_state.py stop",
           "timeoutSec": 5
         }
       ]
     }
   }
   ```

2. Start a new Copilot CLI session. The tab changes on the first turn.

The script writes nothing to stdout, so the hook contract is untouched, and it
always exits 0 — a coloring hiccup must never break a session.

## Configuration

| Variable | Effect |
| --- | --- |
| `COPILOT_TAB_STATE_DEBUG=1` | Log to `~/.copilot/logs/tab-state.log`. Off by default. Set it before launching Copilot so the hooks, and the watcher they spawn, inherit it. |
| `COPILOT_TAB_STATE_NOTIFY=0` | Suppress notifications, keeping only the tab color or title. |

## Troubleshooting

**The tab never changes colour.** Confirm your terminal is in the support table
above. In iTerm2, check that no profile or theme is overriding the tab colour —
some themes follow the OS appearance and repaint tabs themselves.

**The tab is stuck after a crash.** Run
`python3 tools/copilot_tab_state.py reset` in the affected tab.

**Notifications appear twice.** Set `COPILOT_TAB_STATE_NOTIFY=0` if your
terminal already raises its own notification for the same events.
