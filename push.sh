#!/bin/bash
cd /Users/mohammadkaishmanihar/Downloads/chatgpt_gui_mac
git add .
git commit -m "$1"
branch_name="update-$(date +%s)"
git checkout -b "$branch_name"
git push origin "$branch_name"

