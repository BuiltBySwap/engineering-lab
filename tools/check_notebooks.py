#!/usr/bin/env python3
"""Run every code cell of every session notebook and report what works.

  python tools/check_notebooks.py                         Python cells only (fast, nothing downloaded)
  python tools/check_notebooks.py --kotlin                also %%kotlin cells (needs Java 17+; downloads the compiler once)
  python tools/check_notebooks.py --kotlin --online       also cells that download libraries with @file:DependsOn
  python tools/check_notebooks.py docs/topics/AI-02.ipynb one notebook only

Rules
- Setup cells (they start with ! or %run) and notebook magics other than %%kotlin are skipped.
- A cell marked  "exercise": true  in its metadata is meant to fail until you solve it. It counts as OK
  while it fails with NotImplementedError, and is reported as "solved" once it passes.
- Exit code 1 if any cell fails, so GitHub Actions can show a red cross.
"""
import argparse
import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
ROOT = Path(__file__).resolve().parent.parent


def load_kotlin_runner():
    spec = importlib.util.spec_from_file_location("kotlin_magic", ROOT / "tools" / "kotlin_magic.py")
    module = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(module)
    return module.run_kotlin


def classify(source: str) -> str:
    first = source.lstrip().splitlines()[0] if source.strip() else ""
    if first.startswith("%%kotlin"):
        return "kotlin"
    if first.startswith(("!", "%")) or "\n!" in source or "%run" in source:
        return "setup"
    return "python"


def needs_maven(source: str) -> bool:
    return bool(re.search(r'@file:DependsOn\("[^"/]+:[^"]+"\)', source))


def run_python(source: str, namespace: dict, label: str) -> tuple[bool, str]:
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            exec(compile(source, label, "exec"), namespace)
        return True, buffer.getvalue()
    except ModuleNotFoundError as err:
        return False, f"missing package '{err.name}': pip install {err.name}"
    except Exception as err:  # noqa: BLE001
        tail = "".join(traceback.format_exception_only(type(err), err)).strip()
        return False, f"{buffer.getvalue()}{tail}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("notebooks", nargs="*")
    parser.add_argument("--kotlin", action="store_true", help="run %%kotlin cells")
    parser.add_argument("--online", action="store_true", help="run cells that download libraries (@file:DependsOn)")
    parser.add_argument("--verbose", "-v", action="store_true", help="show cell output")
    args = parser.parse_args()

    paths = [Path(p) for p in args.notebooks] or sorted((ROOT / "docs" / "topics").glob("*.ipynb"))
    run_kotlin = load_kotlin_runner() if args.kotlin else None
    totals = {"ok": 0, "fail": 0, "skipped": 0, "exercise": 0}

    for path in paths:
        nb = json.loads(path.read_text(encoding="utf-8"))
        namespace: dict = {"__name__": "__main__"}
        print(f"\n{path.stem}")
        for index, cell in enumerate(nb["cells"]):
            if cell["cell_type"] != "code":
                continue
            source = "".join(cell["source"])
            kind = classify(source)
            exercise = bool(cell.get("metadata", {}).get("exercise"))
            tag = f"  cell {index:>2} {kind:<6}"
            if kind == "setup":
                print(f"{tag} ⏭  setup cell")
                totals["skipped"] += 1
                continue
            if kind == "kotlin" and run_kotlin is None:
                print(f"{tag} ⏭  needs --kotlin")
                totals["skipped"] += 1
                continue
            if kind == "kotlin" and needs_maven(source) and not args.online:
                print(f"{tag} ⏭  downloads libraries: needs --online")
                totals["skipped"] += 1
                continue

            started = time.time()
            if kind == "kotlin":
                buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer):
                    code = run_kotlin(source.split("\n", 1)[1] if "\n" in source else "", 600)
                ok, output = code == 0, buffer.getvalue()
            else:
                ok, output = run_python(source, namespace, f"{path.stem}:cell{index}")
            seconds = time.time() - started

            if exercise:
                if ok:
                    print(f"{tag} 🎉 exercise solved ({seconds:.1f}s)")
                    totals["ok"] += 1
                elif "NotImplementedError" in output:
                    print(f"{tag} ✏️  exercise not solved yet (expected)")
                    totals["exercise"] += 1
                else:
                    print(f"{tag} ❌ exercise failed for another reason\n{indent(output)}")
                    totals["fail"] += 1
            elif ok:
                print(f"{tag} ✅ ({seconds:.1f}s)")
                totals["ok"] += 1
                if args.verbose:
                    print(indent(output))
            else:
                print(f"{tag} ❌ FAILED\n{indent(output)}")
                totals["fail"] += 1

    print(f"\nSummary: {totals['ok']} ok, {totals['fail']} failed, {totals['exercise']} exercises waiting, {totals['skipped']} skipped")
    return 1 if totals["fail"] else 0


def indent(text: str) -> str:
    return "\n".join("      " + line for line in text.strip().splitlines()[-12:])


if __name__ == "__main__":
    sys.exit(main())
