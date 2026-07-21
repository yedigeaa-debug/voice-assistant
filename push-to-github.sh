#!/usr/bin/env bash
# One-shot: create the GitHub monorepo and push. Run from the repo root.
#   ./push-to-github.sh
set -euo pipefail

OWNER="yedigeaa-debug"
REPO="voice-assistant"

if git remote | grep -q origin; then
  echo "origin already set:"; git remote -v; git push -u origin main; exit 0
fi

if command -v gh >/dev/null 2>&1; then
  echo "→ Using GitHub CLI to create $OWNER/$REPO (private) and push…"
  gh auth status >/dev/null 2>&1 || gh auth login
  gh repo create "$OWNER/$REPO" --private --source=. --remote=origin --push
  echo "✅ Done: https://github.com/$OWNER/$REPO"
else
  cat <<EOF
gh (GitHub CLI) not found. Two options:

A) Install gh, then re-run this script:
     brew install gh

B) Create the repo manually:
   1. Open https://github.com/new
      - Owner:  $OWNER
      - Name:   $REPO
      - Private (recommended for coursework)
      - DO NOT add README/.gitignore (we already have them)
   2. Then run:
        git remote add origin https://github.com/$OWNER/$REPO.git
        git push -u origin main
EOF
fi
