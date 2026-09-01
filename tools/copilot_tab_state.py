#!/usr/bin/env python3
"""Show what a Copilot CLI session is doing, in the terminal's own chrome.

Copilot's built-in OSC 9;4 progress indicator only distinguishes "a turn is in
flight" from "no turn is in flight". A turn blocked on a permission prompt is
still in flight, so the spinner keeps spinning and a blocked tab looks exactly
like a busy one -- which is the state you most need to tell apart. This encodes
the distinction in the tab itself.

Two terminals, two channels, because they support different things:

    iTerm2      tab color via OSC 6 (proprietary), notifications via OSC 9
    Metalterm   tab title via OSC 0,               notifications via OSC 777

Both notifications are in-band, so the terminal posts them itself: they are
attributed to the terminal, and clicking one switches to the exact tab that
raised it. Metalterm additionally suppresses its own banner while Metalterm is
frontmost; iTerm2 does not, so this script suppresses that case itself.

    working    amber / "working"      a turn is running
    attention  red   / "NEEDS YOU"    blocked on your approval or input
    idle       blue  / "idle"         turn finished, waiting for you

Hooks give us the turn boundaries (userPromptSubmitted, agentStop), but they
expose no event for "blocked on approval" -- the documented `notification` hook
does not fire for permission prompts in practice. That signal lives only in the
session event stream, so a small watcher tails events.jsonl for
permission.requested and ask_user tool calls.

Commands:
    copilot_tab_state.py working|attention|idle|reset
    copilot_tab_state.py start    # sessionStart: spawn the watcher
    copilot_tab_state.py stop     # sessionEnd: stop the watcher, reset the tab
    copilot_tab_state.py watch --session ID --tty PATH --pid PID --label NAME

Install: see docs/terminal-tab-state.md.

Nothing is written to stdout, so the hook contract is untouched. Always exits 0
-- a coloring hiccup must never break the session.

Environment:
    COPILOT_TAB_STATE_DEBUG=1   log to ~/.copilot/logs/tab-state.log (off by
                                default; set it before launching Copilot so the
                                hooks and the watcher they spawn inherit it)
    COPILOT_TAB_STATE_NOTIFY=0  suppress notifications, keeping only the tab
                                color or title
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

COLORS = {
    "working": (218, 150, 30),
    "attention": (220, 45, 45),
    "idle": (45, 110, 215),
}

# Metalterm has no tab color, so state rides in the title. Marker first: tab
# titles truncate from the right, and the state is what you scan for.
TITLES = {
    "working": "\u25cf working",
    "attention": "\u25b2 NEEDS YOU",
    "idle": "\u25cb idle",
}

CONFIG_DIR = Path(os.environ.get("COPILOT_CONFIG_DIR", Path.home() / ".copilot"))
STATE_DIR = CONFIG_DIR / "run" / "tab-state"
LOG = Path(os.environ.get("COPILOT_TAB_STATE_LOG", CONFIG_DIR / "logs" / "tab-state.log"))
LOG_MAX_BYTES = 256 * 1024

POLL_SECONDS = 0.25
# Watcher exits on its own if the session's copilot process disappears, so a
# hard kill can never strand it.
ORPHAN_CHECK_SECONDS = 5.0
# Repeated approval prompts in a tight loop should not stack up toasts.
NOTIFY_DEBOUNCE_SECONDS = 20.0


def log(message: str) -> None:
    """Append a debug line. Off unless COPILOT_TAB_STATE_DEBUG=1.

    Set it before launching Copilot so the hooks and the watcher they spawn
    both inherit it.
    """
    if os.environ.get("COPILOT_TAB_STATE_DEBUG") != "1":
        return
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        if LOG.exists() and LOG.stat().st_size > LOG_MAX_BYTES:
            LOG.unlink()
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with LOG.open("a") as fh:
            fh.write(f"{stamp} [{os.getpid()}] {message}\n")
    except Exception:
        pass


def process_alive(pid: int) -> bool:
    """Whether pid still exists.

    os.kill(pid, 0) is atomic and cannot time out. The obvious alternative --
    shelling out to ps -- fails open in the wrong direction: under load the
    subprocess can time out and report a perfectly healthy process as dead,
    which silently kills the watcher and takes every state signal with it.
    Anything ambiguous is treated as alive, so the guard only ever fires on a
    definite ProcessLookupError.
    """
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, just owned by another user
    except Exception:
        return True  # unknown; never exit on ambiguity


def ps_field(pid: int, fmt: str) -> str | None:
    try:
        out = subprocess.run(
            ["ps", "-o", fmt, "-p", str(pid)],
            capture_output=True, text=True, timeout=3,
        )
    except Exception:
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def find_copilot() -> tuple[str | None, int | None]:
    """Walk up the process tree to the first ancestor owning a tty.

    Hooks are spawned without a tty of their own; the copilot process that owns
    the tab has one.
    """
    pid = os.getppid()
    for _ in range(10):
        if pid <= 1:
            return None, None
        raw = ps_field(pid, "ppid=,tty=")
        if not raw:
            return None, None
        parts = raw.split()
        if len(parts) < 2:
            return None, None
        ppid, tty = parts[0], parts[1]
        if tty and tty != "??":
            path = f"/dev/{tty}"
            return (path if os.path.exists(path) else None), pid
        try:
            pid = int(ppid)
        except ValueError:
            return None, None
    return None, None


def terminal_kind() -> str | None:
    """Which state channel this terminal supports, or None if unsupported."""
    prog = (os.environ.get("TERM_PROGRAM") or "").lower()
    if prog == "iterm.app":
        return "iterm"
    if prog == "metalterm":
        return "metalterm"
    return None


def escape_for(state: str, kind: str, label: str = "") -> str:
    if kind == "metalterm":
        # OSC 0 sets the title. Verified against Metalterm 0.1.6; OSC 6 (color)
        # and OSC 9;4 (progress) are absent from its binary and do nothing.
        if state == "reset":
            return f"\033]0;{label}\a" if label else "\033]0;\a"
        marker = TITLES[state]
        return f"\033]0;{marker}{f' \u00b7 {label}' if label else ''}\a"

    if state == "reset":
        return "\033]6;1;bg;*;default\a"
    r, g, b = COLORS[state]
    return (
        f"\033]6;1;bg;red;brightness;{r}\a"
        f"\033]6;1;bg;green;brightness;{g}\a"
        f"\033]6;1;bg;blue;brightness;{b}\a"
    )


def notify_escape(title: str, body: str | None, kind: str) -> str:
    """An in-band notification, posted by the terminal itself.

    Both terminals attribute the notification to themselves and, crucially,
    make it a breadcrumb: clicking it switches to the session that posted it
    (verified on iTerm2 -- a notification from a marked tab reopens that exact
    tab). Focus suppression is not symmetric: Metalterm drops the banner while
    it is frontmost (filing it in Notification Center anyway), iTerm2 posts
    regardless. See SUPPRESS_WHEN_FRONTMOST.
    """
    def clean(text: str) -> str:
        out = text.replace("\033", " ").replace("\a", " ")
        return out.replace(";", ",") if kind == "metalterm" else out

    title = clean(title)
    body = clean(body or "Waiting on you")

    if kind == "metalterm":
        # OSC 777 carries a separate title and body.
        return f"\033]777;notify;{title};{body}\033\\"
    # iTerm2's OSC 9 takes a single message, and iTerm2 already prefixes it with
    # the session name and window title -- so repeating "Copilot needs you" here
    # only pushes the actionable part further toward the truncation point.
    return f"\033]9;{body}\a"


def paint(state: str, tty: str | None, kind: str, label: str = "") -> None:
    """One-shot paint by path. Used by the short-lived hook invocations."""
    if not tty:
        return
    try:
        with open(tty, "w") as fh:
            fh.write(escape_for(state, kind, label))
            fh.flush()
    except Exception as exc:
        log(f"paint failed state={state} tty={tty}: {exc}")


def paint_fd(state: str, fd: int, kind: str, label: str = "") -> bool:
    """Paint through a held file descriptor. Returns False once the pty is gone.

    The long-lived watcher must not re-open the tty by path. Closing a terminal
    tab does not promptly kill the process that lived in it, and the freed
    /dev/ttysNNN slot can be handed to a new tab -- so a path-based write from a
    lagging watcher can land on somebody else's tab. A descriptor is bound to
    the original pty, so once that pty is torn down writes can only fail (EIO),
    never land somewhere new. That failure is also the most honest "my tab
    closed" signal available.
    """
    return write_fd(escape_for(state, kind, label), fd)


def write_fd(payload: str, fd: int) -> bool:
    try:
        os.write(fd, payload.encode())
        return True
    except OSError as exc:
        log(f"tty write failed ({exc.errno}); pty is gone")
        return False
    except Exception as exc:
        log(f"tty write error: {exc}")
        return False


def read_payload() -> dict:
    try:
        if sys.stdin.isatty():
            return {}
        raw = sys.stdin.read()
    except Exception:
        return {}
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}



# --------------------------------------------------------------------------
# watcher
# --------------------------------------------------------------------------

def notify(title: str, body: str | None, kind: str, fd: int | None = None) -> None:
    """Post a notification through the terminal.

    Only used for the attention state. Copilot's own notifications setting fires
    on every turn end, which is too noisy to leave on; being blocked on approval
    is rare and always actionable, so it earns an interrupt.

    No focus check on purpose. iTerm2 posts OSC 9 regardless of focus, so a
    prompt in the tab you are already looking at still raises a banner; that is
    wanted here, since the banner is what carries the command text and the
    click-through. Metalterm drops its own banner while Metalterm is frontmost
    and files it in Notification Center instead -- its call, not ours.
    """
    if os.environ.get("COPILOT_TAB_STATE_NOTIFY") == "0":
        return
    if fd is None:
        return
    if write_fd(notify_escape(title, body, kind), fd):
        log(f"notified in-band ({kind}): {title} / {body}")


def events_path(session_id: str) -> Path:
    return CONFIG_DIR / "session-state" / session_id / "events.jsonl"


def pidfile(session_id: str) -> Path:
    return STATE_DIR / f"{session_id}.pid"


def classify_event(event: dict, pending: set) -> tuple[str | None, str | None]:
    """Return (new state, detail) for this event.

    A state of None means leave the color alone. The detail is short context for
    the attention notification, such as what Copilot is asking to run.
    """
    etype = event.get("type")
    data = event.get("data") or {}

    if etype == "permission.requested":
        request = data.get("permissionRequest") or {}
        detail = request.get("intention") or request.get("fullCommandText")
        if isinstance(detail, str):
            detail = " ".join(detail.split())
            if len(detail) > 110:
                detail = detail[:107] + "..."
            # The intention reads as a statement ("Check size of /tmp"); say
            # what is being asked of you, since on iTerm2 this is the only text
            # that survives its own session prefix.
            detail = f"Approve: {detail}"
        else:
            detail = "Approve a pending command"
        return "attention", detail

    if etype == "permission.completed":
        return "working", None

    # ask_user and MCP elicitations block the turn the same way a permission
    # prompt does, but arrive as ordinary tool calls.
    if etype == "tool.execution_start":
        if data.get("toolName") in ("ask_user", "elicitation"):
            call_id = data.get("toolCallId")
            if call_id:
                pending.add(call_id)
            return "attention", "Copilot has a question"
        return None, None

    if etype == "tool.execution_complete":
        call_id = data.get("toolCallId")
        if call_id and call_id in pending:
            pending.discard(call_id)
            return "working", None
        return None, None

    return None, None


def watch(session_id: str, tty: str, pid: int, kind: str, label: str) -> int:
    path = events_path(session_id)
    log(f"watch start session={session_id} tty={tty} pid={pid} kind={kind} label={label}")

    # Hold one descriptor for the life of the watcher: see paint_fd.
    try:
        fd = os.open(tty, os.O_WRONLY | os.O_NOCTTY)
    except Exception as exc:
        log(f"watch abort: cannot open {tty}: {exc}")
        return 0

    pending: set[str] = set()
    offset = path.stat().st_size if path.exists() else 0
    buffer = ""
    last_orphan_check = time.time()
    current = None
    last_notified = 0.0

    try:
        while True:
            time.sleep(POLL_SECONDS)

            now = time.time()
            if now - last_orphan_check >= ORPHAN_CHECK_SECONDS:
                last_orphan_check = now
                # Backstop for "copilot died but the tab is still open". The
                # tab-closed case is caught by the write failing instead.
                if not process_alive(pid):
                    log("watch exit: copilot process gone")
                    paint_fd("reset", fd, kind, label)
                    return 0

            try:
                size = path.stat().st_size
            except FileNotFoundError:
                continue

            if size < offset:  # rotated or truncated
                offset = 0
                buffer = ""
            if size == offset:
                continue

            try:
                with path.open("r", errors="replace") as fh:
                    fh.seek(offset)
                    chunk = fh.read()
                    offset = fh.tell()
            except Exception as exc:
                log(f"watch read failed: {exc}")
                continue

            buffer += chunk
            lines = buffer.split("\n")
            buffer = lines.pop()  # last element is an incomplete line

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except Exception:
                    continue
                state, detail = classify_event(event, pending)
                if not state:
                    continue

                log(f"watch {event.get('type')} -> {state}")
                if not paint_fd(state, fd, kind, label):
                    log("watch exit: tab closed")
                    return 0

                # Notify only on the transition into attention, never on turn end.
                if state == "attention" and current != "attention":
                    now = time.time()
                    if now - last_notified >= NOTIFY_DEBOUNCE_SECONDS:
                        last_notified = now
                        notify("Copilot needs you", detail, kind, fd)
                current = state
    finally:
        try:
            os.close(fd)
        except Exception:
            pass


def spawn_watcher(session_id: str, tty: str, pid: int, kind: str, label: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    stop_watcher(session_id, reset_tty=None, kind=kind, label=label)

    cmd = [
        sys.executable, os.path.abspath(__file__), "watch",
        "--session", session_id, "--tty", tty, "--pid", str(pid),
        "--kind", kind, "--label", label,
    ]
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as exc:
        log(f"spawn failed: {exc}")
        return
    try:
        pidfile(session_id).write_text(str(proc.pid))
    except Exception:
        pass
    log(f"spawned watcher pid={proc.pid} session={session_id}")


def stop_watcher(session_id: str, reset_tty: str | None, kind: str, label: str = "") -> None:
    pf = pidfile(session_id)
    try:
        old = int(pf.read_text().strip())
    except Exception:
        old = None
    if old:
        try:
            os.kill(old, signal.SIGTERM)
            log(f"stopped watcher pid={old}")
        except ProcessLookupError:
            pass
        except Exception as exc:
            log(f"stop failed pid={old}: {exc}")
    try:
        pf.unlink()
    except Exception:
        pass
    if reset_tty:
        paint("reset", reset_tty, kind, label)


# --------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    command = argv[1] if len(argv) > 1 else "idle"

    if command == "watch":
        args = dict(zip(argv[2::2], argv[3::2]))
        session = args.get("--session")
        tty = args.get("--tty")
        pid = args.get("--pid")
        if not (session and tty and pid):
            return 0
        return watch(session, tty, int(pid), args.get("--kind") or "iterm",
                     args.get("--label") or "")

    kind = terminal_kind()
    if not kind:
        return 0

    payload = read_payload()
    label = Path(payload.get("cwd") or os.getcwd()).name

    if command in ("start", "stop"):
        session = payload.get("sessionId")
        if not session:
            log(f"{command}: no sessionId in payload")
            return 0
        tty, pid = find_copilot()
        if command == "start":
            if tty and pid:
                spawn_watcher(session, tty, pid, kind, label)
            else:
                log("start: no ancestor tty; watcher not spawned")
        else:
            stop_watcher(session, reset_tty=tty, kind=kind, label=label)
        return 0

    if command not in COLORS and command != "reset":
        log(f"unknown state {command!r}")
        return 0

    tty, _ = find_copilot()
    if not tty:
        log(f"skip state={command}: no ancestor tty")
        return 0
    paint(command, tty, kind, label)
    log(f"state={command} tty={tty} kind={kind}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as exc:  # never break the session
        log(f"unhandled: {exc}")
        sys.exit(0)
