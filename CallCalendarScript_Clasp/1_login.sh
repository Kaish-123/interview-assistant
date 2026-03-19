#!/usr/bin/env bash
# Step 1: Log in to clasp.
# Open the URL it prints in your browser → sign in → Allow. Then this command will finish.
set -e
cd "$(dirname "$0")"
echo "=== Step 1: clasp login ==="
echo "When the URL appears, open it in your browser and authorize."
echo ""
clasp login
echo ""
echo "Step 1 done. Next: put your Script ID in script_id.txt, then run ./2_clone.sh"
