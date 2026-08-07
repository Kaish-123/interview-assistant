#!/bin/bash
# Self-healing launcher for cron_send_messages.py
# Finds Python dynamically regardless of which version/framework is installed

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Find Python — try multiple known locations
PYTHON=""
for candidate in \
    "$DIR/venv/bin/python3" \
    "$DIR/venv/bin/python" \
    "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.10/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3" \
    "/opt/homebrew/bin/python3" \
    "/usr/local/bin/python3" \
    "/usr/bin/python3"
do
    if [ -x "$candidate" ] && "$candidate" -c "import sys; sys.exit(0)" 2>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "[run_send.sh] ERROR: No working Python found" >&2
    exit 1
fi

echo "[run_send.sh] Using Python: $PYTHON"

# Use venv site-packages if they exist (works even if venv symlink is broken)
SITE_PKGS="$DIR/venv/lib/python$(${PYTHON} -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')/site-packages"
if [ -d "$SITE_PKGS" ]; then
    export PYTHONPATH="$SITE_PKGS:$PYTHONPATH"
    echo "[run_send.sh] Using site-packages: $SITE_PKGS"
fi

exec "$PYTHON" "$DIR/cron_send_messages.py"
