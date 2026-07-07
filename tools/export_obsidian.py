#!/usr/bin/env python3
"""Project waddy private tracking into an Obsidian vault (Option A: projection).

state.json remains the operational source of truth. This generator OWNS the
`Work/` subtree of the target vault and rewrites it on each run. Hand-authored
notes elsewhere in the vault are never touched.

Usage:
    python3 tools/export_obsidian.py [--vault PATH] [--dry-run]

Defaults:
    private dir : <repo>/private
    vault       : ~/src/notes/github-notes
    output root : <vault>/Work
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_PRIVATE = REPO / "private"
DEFAULT_VAULT = Path("~/src/notes/github-notes").expanduser()

# Standalone note dirs -> vault subfolder. scratch/ and notifications/ excluded.
STANDALONE = {
    "notes": "Topics",
    "meetings": "Meetings",
    "slack": "Slack",
    "summaries": "Summaries",
}

# populated in main() before render_task uses it
tasks_ref_title: dict[str, str] = {}


def slugify_keep(name: str) -> str:
    """Make a filesystem/Obsidian-safe file stem, preserving readability."""
    stem = re.sub(r"[\\/:*?\"<>|#^\[\]]", "-", name).strip()
    stem = re.sub(r"\s+", " ", stem).strip(" .-")
    return stem or "untitled"


def yaml_scalar(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if s == "":
        return '""'
    if re.search(r"[:#\[\]{}&*!|>'\"%@`,]|^\s|\s$|^-", s):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def yaml_list(items) -> str:
    items = [i for i in (items or []) if i not in (None, "")]
    if not items:
        return "[]"
    return "[" + ", ".join(yaml_scalar(i) for i in items) + "]"


def date_only(ts: str | None) -> str | None:
    if not ts:
        return None
    return ts[:10]


def fmt_ts(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts[:16].replace("T", " ")


def read_task_notes(private: Path, tid: str) -> list[tuple[str, str]]:
    tdir = private / "tasks" / tid
    out = []
    if tdir.is_dir():
        for f in sorted(tdir.glob("*.md")):
            out.append((f.name, f.read_text(encoding="utf-8", errors="replace")))
    return out


def build_related(tasks: dict) -> dict[str, set[str]]:
    """Link tasks that share an issue or any link URL."""
    by_key: dict[tuple, set[str]] = {}
    for tid, t in tasks.items():
        keys = set()
        if t.get("issue"):
            keys.add(("issue", t["issue"]))
        if t.get("pr"):
            keys.add(("pr", t["pr"]))
        for l in t.get("links", []) or []:
            keys.add(("link", l))
        for k in keys:
            by_key.setdefault(k, set()).add(tid)
    related: dict[str, set[str]] = {tid: set() for tid in tasks}
    for tids in by_key.values():
        if len(tids) > 1:
            for a in tids:
                related[a] |= (tids - {a})
    return related


def issue_link(ref: str) -> str:
    m = re.match(r"([\w.-]+)/([\w.-]+)#(\d+)$", ref or "")
    if m:
        owner, repo, num = m.groups()
        return f"[{ref}](https://github.com/{owner}/{repo}/issues/{num})"
    return ref or ""


def render_task(tid, t, focus_id, related, private) -> str:
    status = t.get("status") or "unknown"
    kind = t.get("kind") or ""
    is_focus = (tid == focus_id)
    tags = ["task", f"status/{status}"] + ([f"kind/{kind}"] if kind else []) + (["focus"] if is_focus else [])
    fm = [
        "---",
        f"id: {yaml_scalar(tid)}",
        f"title: {yaml_scalar(t.get('title', tid))}",
        f"status: {yaml_scalar(status)}",
        f"kind: {yaml_scalar(kind)}",
        f"focus: {yaml_scalar(is_focus)}",
        f"started: {yaml_scalar(date_only(t.get('started_at')))}",
        f"last_touched: {yaml_scalar(date_only(t.get('last_touched_at')))}",
        f"completed: {yaml_scalar(date_only(t.get('completed_at')))}",
        f"issue: {yaml_scalar(t.get('issue'))}",
        f"pr: {yaml_scalar(t.get('pr'))}",
        f"board_url: {yaml_scalar(t.get('board_item_url') or t.get('board_url'))}",
        f"sessions: {yaml_list(t.get('copilot_session_ids'))}",
        f"links: {yaml_list(t.get('links'))}",
        f"tags: {yaml_list(tags)}",
        "---",
        "",
    ]
    body = [f"# {t.get('title', tid)}", ""]
    bits = [f"**status:** {status}", f"**kind:** {kind or '—'}"]
    if is_focus:
        bits.append("**★ focus**")
    if t.get("issue"):
        bits.append(f"**issue:** {issue_link(t['issue'])}")
    if t.get("pr"):
        bits.append(f"**pr:** {issue_link(t['pr'])}")
    body.append(" · ".join(bits))
    body.append("")

    if t.get("links"):
        body.append("**Links:** " + " · ".join(f"<{l}>" for l in t["links"]))
        body.append("")
    if t.get("next_action"):
        body += ["> [!todo] Next action", f"> {t['next_action']}", ""]
    if t.get("outcome"):
        body += ["> [!success] Outcome", f"> {t['outcome']}", ""]

    rel = sorted(related.get(tid, set()))
    if rel:
        body.append("## Related")
        for r in rel:
            body.append(f"- [[Work/Tasks/{r}|{tasks_ref_title.get(r, r)}]]")
        body.append("")

    note_files = read_task_notes(private, tid)
    if note_files:
        body += ["## Notes", ""]
        for fname, content in note_files:
            if len(note_files) > 1:
                body += [f"### {fname}", ""]
            body.append(content.rstrip())
            body.append("")

    touches = t.get("touches") or []
    if touches:
        body.append("## Log")
        for x in reversed(touches):
            when = fmt_ts(x.get("at", ""))
            via = f" _({x['via']})_" if x.get("via") else ""
            note = (x.get("note") or "").strip()
            body.append(f"- **{when}**{via} — {note}")
        body.append("")

    return "\n".join(fm + body).rstrip() + "\n"


def render_standalone(src: Path, subfolder: str) -> str:
    content = src.read_text(encoding="utf-8", errors="replace")
    fm = [
        "---",
        f"source: {yaml_scalar('private/' + src.parent.name + '/' + src.name)}",
        f"tags: {yaml_list([subfolder.lower()])}",
        "---",
        "",
    ]
    if not content.lstrip().startswith("#"):
        fm.append(f"# {src.stem}\n")
    return "\n".join(fm) + content.rstrip() + "\n"


def render_indexes(tasks, focus_id, active, paused, completed_ids) -> dict[str, str]:
    def line(tid):
        t = tasks.get(tid, {})
        return f"- [[Work/Tasks/{tid}|{t.get('title', tid)}]] — {t.get('status','?')}"

    out = {}
    lines = ["---", "tags: [index]", "---", "", "# Active work", ""]
    if focus_id:
        lines += ["## ★ Focus", line(focus_id), ""]
    lines += ["## Active", *[line(t) for t in active if t != focus_id], ""]
    if paused:
        lines += ["## Paused", *[line(t) for t in paused], ""]
    out["Active.md"] = "\n".join(lines).rstrip() + "\n"

    by_status: dict[str, list[str]] = {}
    for tid, t in tasks.items():
        by_status.setdefault(t.get("status", "unknown"), []).append(tid)
    lines = ["---", "tags: [index]", "---", "", "# Tasks by status", ""]
    for st in sorted(by_status):
        lines.append(f"## {st} ({len(by_status[st])})")
        lines += [line(t) for t in sorted(by_status[st])]
        lines.append("")
    out["By-status.md"] = "\n".join(lines).rstrip() + "\n"

    lines = ["---", "tags: [index]", "---", "", "# Recently completed", ""]
    lines += [line(t) for t in completed_ids]
    out["Recently-completed.md"] = "\n".join(lines).rstrip() + "\n"

    out["Dashboard (Dataview).md"] = (
        "---\ntags: [index]\n---\n\n# Dashboard\n\n"
        "> Requires the Dataview community plugin.\n\n"
        "## Active / paused\n"
        "```dataview\ntable status, kind, last_touched\n"
        'from "Work/Tasks"\nwhere status != "done"\nsort last_touched desc\n```\n\n'
        "## Recently touched\n"
        "```dataview\ntable status, last_touched\n"
        'from "Work/Tasks"\nsort last_touched desc\nlimit 20\n```\n'
    )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--private", type=Path, default=DEFAULT_PRIVATE)
    ap.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    private = args.private.expanduser()
    vault = args.vault.expanduser()
    work = vault / "Work"

    state = json.loads((private / "state.json").read_text(encoding="utf-8"))
    tasks = state.get("tasks", {})
    focus_id = state.get("focus")
    active = state.get("active_tasks", []) or []
    paused = state.get("paused_tasks", []) or []
    completed_ids = [c.get("id") for c in state.get("recent_completed", []) if c.get("id")]

    global tasks_ref_title
    tasks_ref_title = {tid: t.get("title", tid) for tid, t in tasks.items()}
    related = build_related(tasks)

    files: dict[str, str] = {}
    for tid, t in tasks.items():
        files[f"Tasks/{tid}.md"] = render_task(tid, t, focus_id, related, private)
    for dirname, subfolder in STANDALONE.items():
        d = private / dirname
        if d.is_dir():
            for f in sorted(d.glob("*.md")):
                files[f"{subfolder}/{slugify_keep(f.stem)}.md"] = render_standalone(f, subfolder)
    for name, content in render_indexes(tasks, focus_id, active, paused, completed_ids).items():
        files[f"_index/{name}"] = content

    counts: dict[str, int] = {}
    for rel in files:
        counts[rel.split("/", 1)[0]] = counts.get(rel.split("/", 1)[0], 0) + 1
    print(f"Source : {private}")
    print(f"Vault  : {work}")
    print(f"Would write {len(files)} files:", dict(sorted(counts.items())))

    if args.dry_run:
        print("\n[dry-run] no files written. Sample paths:")
        for rel in list(files)[:8]:
            print("  Work/" + rel)
        return

    if work.exists():
        shutil.rmtree(work)
    for rel, content in files.items():
        dest = work / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
    print(f"\nWrote {len(files)} files to {work}")


if __name__ == "__main__":
    main()
