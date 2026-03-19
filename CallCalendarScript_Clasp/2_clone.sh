#!/usr/bin/env bash
# Step 2: Clone the project. Uses Script ID from script_id.txt or first argument.
# Either: echo YOUR_SCRIPT_ID > script_id.txt   then run ./2_clone.sh
# Or:     ./2_clone.sh YOUR_SCRIPT_ID
set -e
cd "$(dirname "$0")"
SCRIPT_ID="${1:-$(cat script_id.txt 2>/dev/null || true)}"
if [[ -z "$SCRIPT_ID" ]]; then
  echo "Usage: ./2_clone.sh YOUR_SCRIPT_ID"
  echo "Or:   echo YOUR_SCRIPT_ID > script_id.txt   then   ./2_clone.sh"
  exit 1
fi
echo "=== Step 2: clasp clone $SCRIPT_ID ==="
clasp clone "$SCRIPT_ID"
echo ""
echo "Clone done. You can now run 'clasp push' from this folder to deploy changes."
