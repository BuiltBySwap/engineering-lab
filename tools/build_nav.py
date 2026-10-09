#!/usr/bin/env python3
"""Build the left-hand menu, organised by TOPIC (Android, Backend, DSA, Python, AI, ...).

Reads docs/progress.json (sessions, written by build_index.py).
Writes (generated, not committed):
  docs/SUMMARY.md                       the menu (read by the mkdocs-literate-nav plugin)
  docs/.generated/sessions-<topic>.md   the session table shown on each topic's overview page

A session's topic comes from the `track` field of its status card. New sessions appear in the right
topic automatically: no menu editing.
Run order: build_index.py, build_book.py, build_nav.py, then mkdocs build.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ICON = {"done": "✅", "partial": "🟡", "in-progress": "🟡", "not-started": "⬜"}

# (key, menu title, overview page). The order here is the order in the menu.
TOPICS = [
    ("android", "Android", "android/index.md"),
    ("backend", "Backend", "backend/index.md"),
    ("dsa", "DSA", "dsa/index.md"),
    ("python", "Python", "python/index.md"),
    ("ai", "AI", "ai/index.md"),
    ("system-design", "System design", "system-design/index.md"),
    ("rn", "React Native", "rn/index.md"),
]
TRACK_TO_TOPIC = {
    "android": "android", "kotlin": "android", "compose": "android",
    "backend": "backend", "ktor": "backend", "devops": "backend",
    "dsa": "dsa",
    "python": "python",
    "ai": "ai",
    "system-design": "system-design",
    "rn": "rn", "react-native": "rn",
    "portfolio": "projects",
    "setup": "tools", "lab": "tools",
}
EXTRA_PAGES = {"android": [("Production app architecture", "android/architecture.md")]}


def label(session: dict) -> str:
    return f"{session['id']} · {re.split(r' \(|: ', session['title'])[0]}"


def main() -> None:
    progress = DOCS / "progress.json"
    if not progress.exists():
        sys.exit("ERROR: docs/progress.json is missing. Run tools/build_index.py first.")
    sessions = json.loads(progress.read_text(encoding="utf-8"))["sessions"]
    by_topic: dict[str, list[dict]] = {}
    for s in sessions:
        by_topic.setdefault(TRACK_TO_TOPIC.get(s["track"].lower(), "tools"), []).append(s)

    # ----- per-topic session tables (included by the topic overview pages) -----
    frag_dir = DOCS / ".generated"
    frag_dir.mkdir(exist_ok=True)
    for key, title, _ in TOPICS:
        rows = by_topic.get(key, [])
        lines = []
        if rows:
            lines += ["| Session | Status | Takeaway |", "|---|---|---|"]
            for s in rows:
                lines.append(f"| [{label(s)}](../{s['page']}) | {ICON.get(s['status'], '⬜')} {s['status']} | {s['insight']} |")
        else:
            lines.append("_No sessions yet._")
        (frag_dir / f"sessions-{key}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ----- the menu -----
    out = ["* [Home](index.md)", "* [Start here](start-here.md)", "* [Status](status.md)"]
    for key, title, page in TOPICS:
        out.append(f"* [{title}]({page})")
        out += [f"    * [{label(s)}]({s['page']})" for s in by_topic.get(key, [])]
        out += [f"    * [{t}]({p})" for t, p in EXTRA_PAGES.get(key, [])]

    out += ["* Daily practice", "    * [Mobile Exploration](mobile-exploration/index.md)"]   # categories are linked from its overview
    out += ["    * English",
            "        * [Word of the day](english/index.md)",
            "        * [Vocabulary](english/vocabulary.md)",
            "        * [Error log](english/error-log.md)",
            "    * Role lens",
            "        * [Overview](role-lens/index.md)",
            "        * [Thinking models](role-lens/models.md)"]
    out += ["* Projects", "    * [Code repositories](repos.md)"]
    out += [f"    * [{label(s)}]({s['page']})" for s in by_topic.get("projects", [])]
    out += ["* Tools and setup", "    * [How to run the code](run-the-code.md)"]
    out += [f"    * [{label(s)}]({s['page']})" for s in by_topic.get("tools", [])]
    out += ["    * [Origin-story note template](note-templates/origin-story.md)"]
    out += ["* Index", "    * [All sessions (Progress)](progress.md)", "    * [Tags](tags.md)"]
    (DOCS / "SUMMARY.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"nav built: {len(sessions)} sessions in {len([k for k in by_topic if by_topic[k]])} groups")


if __name__ == "__main__":
    main()
