#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# push.sh  — stage everything and push to GitHub
# Usage:
#   sh push.sh                  → auto commit message with timestamp
#   sh push.sh "your message"   → custom commit message
# ─────────────────────────────────────────────────────────────────────────────
set -e   # exit immediately on any error

REPO_DIR="/Users/mohammadkaishmanihar/Downloads/chatgpt_gui_mac"
cd "$REPO_DIR"

echo "📂 Working in: $REPO_DIR"

# ── 1. Make sure we're on main ─────────────────────────────────────────────
git checkout main 2>/dev/null || true
echo "✅ Branch: $(git branch --show-current)"

# ── 2. Remove files that should never be tracked ──────────────────────────
# (idempotent — silently skips if already untracked)
for f in .DS_Store ui_prefs.json chats.json chats_v2.db interviewer.wav; do
    git rm --cached "$f" 2>/dev/null && echo "🗑 Untracked from git: $f" || true
done

# Also untrack __pycache__ and *.pyc silently
git rm --cached -r __pycache__/ 2>/dev/null || true
git rm --cached '*.pyc' 2>/dev/null || true

# ── 3. Stage all changes ───────────────────────────────────────────────────
git add -A
echo "📦 Staged files:"
git status --short

# ── 4. Skip commit if nothing to commit ────────────────────────────────────
if git diff --cached --quiet; then
    echo "ℹ️  Nothing new to commit — pushing existing commits."
else
    if [ -z "$1" ]; then
        TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
        COMMIT_MSG="UPDATE_$TIMESTAMP"
    else
        COMMIT_MSG="$1"
    fi
    git commit -m "$COMMIT_MSG"
    echo "✅ Committed: $COMMIT_MSG"
fi

# ── 5. Push ────────────────────────────────────────────────────────────────
echo "🚀 Pushing to GitHub..."
git push origin main
echo "✅ Push complete! Repo: $(git remote get-url origin)"
