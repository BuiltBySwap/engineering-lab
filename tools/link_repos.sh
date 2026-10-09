#!/usr/bin/env bash
# Adds a "Learning notes" section to the README of each code repo, linking back to this book.
# Safe to run twice (it checks for a marker). It does NOT commit: review, then commit and push yourself.
#
# Usage: bash tools/link_repos.sh            (repos are expected in ~/dev)
#        DEV_DIR=/other/path bash tools/link_repos.sh
set -u
SITE="https://builtbyswap.github.io/engineering-lab"
DEV="${DEV_DIR:-$HOME/dev}"
MARK="<!-- learning-notes -->"

append() {
  local repo="$1" text="$2" file="$DEV/$1/README.md"
  if [ ! -f "$file" ]; then echo "skip  $repo (no README.md at $file)"; return; fi
  if grep -q "$MARK" "$file"; then echo "ok    $repo (already linked)"; return; fi
  printf '\n%s\n%s\n' "$MARK" "$text" >> "$file"
  echo "added $repo"
}

append kaizen "## Learning notes

The book behind this project: $SITE/

- Android skeleton (MVI + Hilt + tests): [PRJ-01]($SITE/topics/PRJ-01/)
- Ktor server v0: [BE-02]($SITE/topics/BE-02/), how a backend works: [BE-01]($SITE/topics/BE-01/)
- Status and what is next: [Status]($SITE/status/)"

append kotlin-dsa-kata "## Learning notes

The book behind this repo: $SITE/

- Binary search: [DSA-01]($SITE/topics/DSA-01/)
- Restart day and repo setup: [DD-01]($SITE/topics/DD-01/)
- Run Kotlin cells in Colab: [LAB-01]($SITE/topics/LAB-01/)
- DSA section: [DSA]($SITE/dsa/)"

append repo-template "## Learning notes

How this template was set up: [W0-4]($SITE/topics/W0-4/)"

echo
echo "Next: review with 'git diff' in each repo, then commit and push."
