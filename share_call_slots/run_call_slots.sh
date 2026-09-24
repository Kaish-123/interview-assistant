#!/bin/zsh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$DIR/call_slots.py" --days "${1:-3}" --whatsapp
