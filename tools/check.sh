#!/usr/bin/env bash
# Full health check: build the site strictly, then run every code cell of every notebook.
# Usage: bash tools/check.sh              (Python + offline Kotlin cells)
#        bash tools/check.sh --online     (also cells that download libraries)
set -e
cd "$(dirname "$0")/.."
if [ ! -d .venv ]; then echo "No .venv yet. Run first:  bash tools/setup_local.sh"; exit 1; fi
source .venv/bin/activate
python tools/build_index.py && python tools/build_book.py && python tools/build_nav.py
mkdocs build --strict
python tools/check_notebooks.py --kotlin "$@"
