#!/bin/bash
cd /Users/mohammadkaishmanihar/Downloads/chatgpt_gui_mac

# Ensure you're on main branch
git checkout main

# Clean .env from git tracking and ignore it
git rm --cached .env 2>/dev/null
echo ".env" >> .gitignore
git add .gitignore

# Add and commit
git add .
git commit -m "$1"

# Push to main
git push origin main

