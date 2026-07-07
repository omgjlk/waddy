#!/usr/bin/env python3
"""Append a session-lifecycle entry to waddy's session ledger.

Invoked by a Copilot CLI user-level hook on sessionStart / sessionEnd. Reads the
hook payload JSON from stdin and appends one enriched JSONL line to the ledger.
Gives waddy a deterministic, lossless index of "which session ran where, when" —
independent of session-store compaction.

Usage (from a hook):
    python3 tools/session_ledger.py start   # sessionStart
    python3 tools/session_ledger.py end     # sessionEnd
    python3 tools/session_ledger.py claim   # userPromptSubmitted (binds task<->session)

Payload (camelCase hook events), on stdin:
    sessionStart:        {sessionId, timestamp(ms), cwd, source, initialPrompt?}
    sessionEnd:          {sessionId, timestamp(ms), cwd, reason}
    userPromptSubmitted: {sessionId, timestamp(ms), cwd, prompt}
        -> a 'claim' entry is written ONLY when the prompt contains a
           `waddy-task:<id>` marker (as emitted by a start-worker brief),
           capturing the task<->session binding at pickup time.

Ledger path: $WADDY_SESSION_LEDGER, else <repo>/private/session-ledger.jsonl.
Always exits 0 — a ledger hiccup must never break the user's session.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_LEDGER = REPO / "private" / "session-ledger.jsonl"

# A worker brief carries this marker so a pasted prompt binds task <-> session.
TASK_MARKER = re.compile(r"waddy-task:\s*([0-9A-Za-z._\-]+)")


def git(cwd: str, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", cwd, *args],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0:
            return out.stdout.strip() or None
    except Exception:
        pass
    return None


def iso_from_ms(ms) -> str | None:
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()
    except Exception:
        return None


def main() -> int:
    event = sys.argv[1] if len(sys.argv) > 1 else "unknown"

    raw = ""
    try:
        raw = sys.stdin.read()
    except Exception:
        pass
    payload = {}
    if raw.strip():
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"_unparsed_stdin": raw[:500]}

    # Accept both camelCase and snake_case field names defensively.
    sid = payload.get("sessionId") or payload.get("session_id")
    cwd = payload.get("cwd") or os.getcwd()
    ts_payload = payload.get("timestamp")
    payload_iso = iso_from_ms(ts_payload) if isinstance(ts_payload, (int, float)) else (
        ts_payload if isinstance(ts_payload, str) else None
    )

    # 'claim' = userPromptSubmitted. Only record a binding when the prompt
    # carries a `waddy-task:` marker (e.g. a pasted worker brief). This keeps
    # arbitrary prompt content out of the ledger and captures the task<->session
    # binding at pickup time, before any work — so it survives a crash.
    if event == "claim":
        prompt = payload.get("prompt") or ""
        m = TASK_MARKER.search(prompt)
        if not m:
            return 0  # no marker → nothing to record, stay quiet
        entry = {
            "event": "claim",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "session_id": sid,
            "cwd": cwd,
            "task_id": m.group(1),
            "payload_ts": payload_iso,
        }
        top = git(cwd, "rev-parse", "--show-toplevel")
        if top:
            entry["repo"] = Path(top).name
            entry["branch"] = git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
        ledger = Path(os.environ.get("WADDY_SESSION_LEDGER", str(DEFAULT_LEDGER)))
        try:
            ledger.parent.mkdir(parents=True, exist_ok=True)
            with ledger.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass
        return 0

    entry = {
        "event": event,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "session_id": sid,
        "cwd": cwd,
        "source": payload.get("source"),        # sessionStart only
        "reason": payload.get("reason"),         # sessionEnd only
        "payload_ts": payload_iso,
    }
    # Enrich with git context (deterministic, fast).
    top = git(cwd, "rev-parse", "--show-toplevel")
    if top:
        entry["repo"] = Path(top).name
        entry["branch"] = git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
        entry["head"] = git(cwd, "rev-parse", "--short", "HEAD")

    ledger = Path(os.environ.get("WADDY_SESSION_LEDGER", str(DEFAULT_LEDGER)))
    try:
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with ledger.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # never fail the session

    return 0


if __name__ == "__main__":
    sys.exit(main())
