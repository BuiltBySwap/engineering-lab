#!/usr/bin/env python3
"""Create a new topic notebook: notes + examples + runnable code in ONE file.

Usage:
  python tools/new_topic.py AI-03 "Backpropagation" ai
"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "BuiltBySwap/engineering-lab"


def md(text: str, n: int) -> dict:
    return {"cell_type": "markdown", "id": f"m{n}", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text: str, n: int) -> dict:
    return {"cell_type": "code", "id": f"c{n}", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    topic_id, title, track = sys.argv[1:4]
    path = ROOT / "docs" / "topics" / f"{topic_id}.ipynb"
    if path.exists():
        sys.exit(f"{path.name} already exists")
    card = f"""# {topic_id} · {title}

[Open in Colab](https://colab.research.google.com/github/{REPO}/blob/main/docs/topics/{topic_id}.ipynb)

**Status card** (edit it; the Progress and Tags pages are built from it):

```yaml
id: {topic_id}
title: {title}
track: {track}
date: {date.today().isoformat()}
code: ""                 # repo or repo/path, e.g. kaizen/server-ktor
status: in-progress        # not-started | in-progress | partial | done
score: ""                  # quiz score, e.g. 4/5
insight: ""                # ONE sentence you could say in an interview
tags: [{topic_id}, {track}]
pending: []                # open items, one per line
```"""
    cells = [
        md(card, 1),
        md("## Goal\nWhat this session is for, in one or two lines.\n\n## What I learned (plain words)\n", 2),
        md("## Examples\nRun each cell with **Shift + Enter**. Predict before you run.", 3),
        code("# first example\nprint('hello')", 4),
        md("## Bug diary\n\n| Error or symptom | Cause | Fix |\n|---|---|---|\n| | | |", 5),
        md("## Quiz and mistakes\n- Score:\n- What I got wrong, and why:", 6),
        md("## Origin story\n1. Problem:\n2. Old way:\n3. Why it broke:\n4. The invention:\n5. How it works inside:\n6. Where I've used it:\n7. Trade-offs:", 7),
        md("## In my own words\n\n## Next\n", 8),
    ]
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
          "nbformat": 4, "nbformat_minor": 5}
    path.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"created {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
