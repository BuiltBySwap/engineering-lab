#!/usr/bin/env bash
# Shows, for every code repo, what is not committed or not pushed yet.
#
# Usage: bash tools/repo_status.sh            (repos are expected in ~/dev)
#        DEV_DIR=/other/path bash tools/repo_status.sh
set -u
DEV="${DEV_DIR:-$HOME/dev}"
all_clean=1
printf '%-16s %-8s %-12s %s\n' REPO BRANCH UNCOMMITTED UNPUSHED
for name in kaizen kotlin-dsa-kata engineering-lab repo-template BuiltBySwap; do
  dir="$DEV/$name"
  if [ ! -d "$dir/.git" ]; then printf '%-16s not found at %s\n' "$name" "$dir"; continue; fi
  branch=$(git -C "$dir" branch --show-current)
  changed=$(git -C "$dir" status --porcelain | wc -l | tr -d ' ')
  if git -C "$dir" rev-parse --abbrev-ref '@{u}' >/dev/null 2>&1; then
    ahead=$(git -C "$dir" rev-list --count '@{u}..HEAD')
  else
    ahead="no-remote"
  fi
  printf '%-16s %-8s %-12s %s\n' "$name" "$branch" "$changed" "$ahead"
  if [ "$changed" != "0" ] || { [ "$ahead" != "0" ] && [ "$ahead" != "no-remote" ]; }; then all_clean=0; fi
done
echo
if [ "$all_clean" = "1" ]; then echo "Everything is committed and pushed."; else echo "Commit what is uncommitted, then 'git push' where UNPUSHED is above 0."; fi
