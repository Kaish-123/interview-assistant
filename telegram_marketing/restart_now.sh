#!/bin/bash
# ============================================================
# TechyEra Telegram Marketing — Full Restart Script
# Run this ONCE in Terminal to restore the automation.
# After this, everything runs automatically forever.
# ============================================================

BASE="/Users/mohammadkaishmanihar/Downloads/chatgpt_gui_mac/telegram_marketing"
PYTHON="$BASE/venv/bin/python"
AGENTS_DIR="$HOME/Library/LaunchAgents"
SEND_PLIST="com.techyera.telegram.send"
GROWTH_PLIST="com.techyera.telegram.growth"

echo ""
echo "========================================================"
echo "  TechyEra Telegram Marketing — Restart"
echo "  $(date)"
echo "========================================================"

# ── Step 1: Clear any stale SQLite journals ───────────────────────────────────
echo ""
echo "[1/5] Clearing stale session journals..."
for f in "$BASE"/*.session-journal; do
    [ -f "$f" ] && rm -f "$f" && echo "  Removed: $(basename $f)"
done
echo "  Done."

# ── Step 2: Copy plists to LaunchAgents ─────────────────────────────────────
echo ""
echo "[2/5] Installing LaunchAgent plists..."
mkdir -p "$AGENTS_DIR"
cp "$BASE/$SEND_PLIST.plist"   "$AGENTS_DIR/$SEND_PLIST.plist"   && echo "  ✓ Copied $SEND_PLIST.plist"
cp "$BASE/$GROWTH_PLIST.plist" "$AGENTS_DIR/$GROWTH_PLIST.plist" && echo "  ✓ Copied $GROWTH_PLIST.plist"

# ── Step 3: Unload old instances (ignore errors) ─────────────────────────────
echo ""
echo "[3/5] Unloading old service instances (if any)..."
launchctl unload "$AGENTS_DIR/$SEND_PLIST.plist"   2>/dev/null && echo "  Unloaded $SEND_PLIST"
launchctl unload "$AGENTS_DIR/$GROWTH_PLIST.plist" 2>/dev/null && echo "  Unloaded $GROWTH_PLIST"
sleep 2

# ── Step 4: Load / start services ────────────────────────────────────────────
echo ""
echo "[4/5] Loading services..."
launchctl load "$AGENTS_DIR/$SEND_PLIST.plist"
RC_SEND=$?
launchctl load "$AGENTS_DIR/$GROWTH_PLIST.plist"
RC_GROWTH=$?

sleep 2

echo ""
echo "  Status check:"
launchctl list | grep techyera && echo "  ✅ Both services registered." || echo "  ⚠️  Services may not have appeared yet — check again in 30s."

if [ $RC_SEND -eq 0 ] && [ $RC_GROWTH -eq 0 ]; then
    echo "  ✅ Load commands succeeded."
else
    echo "  ⚠️  One or both loads returned non-zero. Check:"
    echo "      launchctl list | grep techyera"
fi

# ── Step 5: Run watchdog immediately to confirm health ────────────────────────
echo ""
echo "[5/5] Running watchdog health check..."
"$PYTHON" "$BASE/telegram_watchdog.py"

echo ""
echo "========================================================"
echo "  ✅ Done! Telegram marketing is now running."
echo ""
echo "  Send messages : every 30 minutes (48x per day)"
echo "  Join groups   : every 4 hours    (6x per day)"
echo "  Watchdog      : daily auto-heal via Cowork scheduler"
echo ""
echo "  To check status anytime:"
echo "    launchctl list | grep techyera"
echo "    tail -20 $BASE/cron_messages.log"
echo "    tail -10 $BASE/cron_growth.log"
echo "========================================================"
