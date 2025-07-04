#!/bin/bash
cd /Users/mohammadkaishmanihar/Downloads/chatgpt_gui_mac

# Ensure you're on main branch
git checkout main

# Clean .env from git tracking and ignore it
git rm --cached .env 2>/dev/null
echo ".env" >> .gitignore
git add .gitignore

# Add all changes
git add .

# Determine commit message
if [ -z "$1" ]; then
  TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
  COMMIT_MSG="FIX_$TIMESTAMP"
else
  COMMIT_MSG="$1"
fi

# Commit and push
git commit -m "$COMMIT_MSG"
git push origin main

