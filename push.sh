#!/bin/bash
cd /Users/mohammadkaishmanihar/Downloads/chatgpt_gui_mac
git add .
git commit -m "$1"

branch="fix-push-$(date +%s)"
git checkout -b "$branch"
git push origin "$branch"

