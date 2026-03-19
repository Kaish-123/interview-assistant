#!/usr/bin/env bash
# Run this AFTER clasp login, with your Script ID.
# Usage: ./clone.sh YOUR_SCRIPT_ID
# Example: ./clone.sh 1a2B3c4D5e6F7g8H9i0J

SCRIPT_ID="${1:?Usage: ./clone.sh YOUR_SCRIPT_ID}"
cd "$(dirname "$0")"
clasp clone "$SCRIPT_ID"
echo "Done. You can now run 'clasp push' from this folder to deploy changes."
