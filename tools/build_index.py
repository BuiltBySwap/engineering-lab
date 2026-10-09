#!/usr/bin/env python3
"""Build the learning index from the topic notebooks.

Every session lives in ONE file: docs/topics/<ID>.ipynb (notes + examples + runnable code).
Its first cell holds a "status card": a fenced ```yaml block with id, title, status, tags...

This script reads those cards and writes:
  docs/progress.md    one row per session + one combined list of open items
  docs/tags.md        every tag with the sessions that carry it
  docs/progress.json  the same data for apps (and for Claude to read)

Run it before `mkdocs build` (the GitHub Action does this for you).
"""
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TOPICS = ROOT / "docs" / "topics"
CARD = re.compile(r"```yaml\s*\n(.*?)\n```", re.S)
STATUSES = ["not-started", "in-progress", "partial", "done"]
REQUIRED = ["id", "title", "track", "date", "status"]
REPO = "BuiltBySwap/engineering-lab"
GH = "https://github.com/BuiltBySwap"


def to_text(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()[:10]
    return "" if value is None else str(value)


def load(path: Path) -> dict:
    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = nb.get("cells", [])
    if not cells or cells[0].get("cell_type") != "markdown":
        sys.exit(f"ERROR {path.name}: the first cell must be a markdown cell with the status card")
    match = CARD.search("".join(cells[0]["source"]))
    if not match:
        sys.exit(f"ERROR {path.name}: the first cell needs a ```yaml status card")
    meta = yaml.safe_load(match.group(1)) or {}
    missing = [key for key in REQUIRED if not meta.get(key)]
    if missing:
        sys.exit(f"ERROR {path.name}: status card is missing: {', '.join(missing)}")
    if str(meta["id"]) != path.stem:
        sys.exit(f"ERROR {path.name}: id '{meta['id']}' must match the file name '{path.stem}'")
    if meta["status"] not in STATUSES:
        sys.exit(f"ERROR {path.name}: status must be one of {STATUSES}, not '{meta['status']}'")
    return {
        "id": str(meta["id"]),
        "title": str(meta["title"]),
        "track": str(meta["track"]),
        "date": to_text(meta["date"]),
        "status": meta["status"],
        "score": to_text(meta.get("score")),
        "insight": to_text(meta.get("insight")).strip(),
        "code": to_text(meta.get("code")).strip(),
        "tags": [str(tag) for tag in (meta.get("tags") or [])],
        "pending": [str(item) for item in (meta.get("pending") or [])],
        "page": f"topics/{path.stem}.ipynb",
        "colab": f"https://colab.research.google.com/github/{REPO}/blob/main/docs/topics/{path.name}",
    }


def main() -> None:
    sessions = sorted((load(p) for p in TOPICS.glob("*.ipynb")), key=lambda s: (s["date"], s["id"]))
    counts = {status: sum(1 for s in sessions if s["status"] == status) for status in STATUSES}

    (ROOT / "docs" / "progress.json").write_text(
        json.dumps({"counts": counts, "sessions": sessions}, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    lines = [
        "# Progress",
        "",
        "> Generated from the status card at the top of every notebook in `docs/topics/`. **Do not edit by hand**: "
        "change a notebook, push, and this page rebuilds.",
        "",
        "**Totals:** " + " · ".join(f"{status}: {n}" for status, n in counts.items()),
        "",
        "| ID | Title | Date | Status | Score | Code | One-line takeaway |",
        "|---|---|---|---|---|---|---|",
    ]
    def code_link(code: str) -> str:
        if not code:
            return ""
        repo, _, path = code.partition("/")
        return f"[{code}]({GH}/{repo}/tree/main/{path})" if path else f"[{code}]({GH}/{repo})"

    for s in sessions:
        lines.append(
            f"| [{s['id']}]({s['page']}) | {s['title']} | {s['date']} | {s['status']} | {s['score']} | {code_link(s['code'])} | {s['insight']} |"
        )

    lines += ["", "## Open items (the parked list)", ""]
    open_items = [s for s in sessions if s["pending"]]
    if not open_items:
        lines.append("Nothing pending.")
    for s in open_items:
        lines.append(f"**[{s['id']}]({s['page']}) · {s['title']}**")
        lines += [f"- [ ] {item}" for item in s["pending"]]
        lines.append("")
    lines += ["", "Browse by [tag](tags.md). Machine-readable copy: `progress.json`.", ""]
    (ROOT / "docs" / "progress.md").write_text("\n".join(lines), encoding="utf-8")

    by_tag: dict[str, list[dict]] = {}
    for s in sessions:
        for tag in s["tags"]:
            by_tag.setdefault(tag, []).append(s)
    tag_lines = ["# Tags", "", "> Generated. Every session carries its ID as a tag (for example `AI-02`), plus its track and keywords.", ""]
    for tag in sorted(by_tag, key=str.lower):
        tag_lines.append(f"## {tag}")
        tag_lines.append("")
        tag_lines += [f"- [{s['id']} · {s['title']}]({s['page']})" for s in by_tag[tag]]
        tag_lines.append("")
    (ROOT / "docs" / "tags.md").write_text("\n".join(tag_lines), encoding="utf-8")

    print(f"index built: {len(sessions)} sessions, {sum(len(s['pending']) for s in sessions)} open items, {len(by_tag)} tags")


if __name__ == "__main__":
    main()
