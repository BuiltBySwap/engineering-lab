#!/usr/bin/env bash
# One-time setup so that every notebook in this repo runs on your computer (VS Code or Jupyter).
# Usage: bash tools/setup_local.sh
set -e
cd "$(dirname "$0")/.."

echo "1/4  Creating the Python environment (.venv)..."
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -q --upgrade pip

echo "2/4  Installing the site tools and the notebook packages..."
pip install -q -r requirements.txt -r requirements-dev.txt

echo "3/4  Registering the notebook kernel..."
python -m ipykernel install --user --name engineering-lab --display-name "Engineering Lab (.venv)" >/dev/null

echo "4/4  Checking Java (only needed for the Kotlin cells)..."
if command -v java >/dev/null 2>&1; then
  major=$(java -version 2>&1 | head -1 | sed -E 's/.*"([0-9]+)(\.([0-9]+))?.*/\1 \3/' | awk '{print ($1==1)?$2:$1}')
  if [ "${major:-0}" -ge 17 ]; then echo "     Java $major found: Kotlin cells will run."
  else echo "     Java $major is too old for Kotlin cells. Install JDK 17 or newer (brew install --cask temurin@21)."; fi
else
  echo "     Java not found: Python cells will run, Kotlin cells need a JDK (brew install --cask temurin@21)."
fi

cat <<'MSG'

Done. Now:
  * VS Code: open this folder, open a notebook in docs/topics/, click "Select Kernel" (top right)
    and choose "Engineering Lab (.venv)". Run cells with Shift+Enter.
  * Check that every code cell runs:   bash tools/check.sh
  * Preview the site:                  source .venv/bin/activate && mkdocs serve
MSG
