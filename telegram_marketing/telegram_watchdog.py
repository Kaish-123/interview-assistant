#!/usr/bin/env python3
"""
TELEGRAM MARKETING WATCHDOG
============================
Daily health-check & auto-heal script for TechyEra Telegram automation.

What it does:
  1. Checks if launchd services are registered (com.techyera.telegram.send / .growth)
  2. Checks log freshness — detects if scripts have gone silent
  3. Auto-heals common issues:
       • Clears stale SQLite .session-journal files (cause "database is locked")
       • Unloads + reloads launchd plists when services are missing or dead
       • Auto-disables targets that keep permanently failing (no-permission, private, invalid ID)
  4. Writes a clear health-report to watchdog.log

Run this script daily (via Cowork scheduler or cron):
  /path/to/venv/bin/python /path/to/telegram_marketing/telegram_watchdog.py
"""

import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
WATCHDOG_LOG = SCRIPT_DIR / "watchdog.log"
FAIL_TRACK_FILE = SCRIPT_DIR / "fail_tracker.json"

SEND_PLIST_NAME = "com.techyera.telegram.send"
GROWTH_PLIST_NAME = "com.techyera.telegram.growth"

# Paths that launchd uses (must match what's inside the .plist files)
SEND_PLIST = Path.home() / "Library/LaunchAgents" / f"{SEND_PLIST_NAME}.plist"
GROWTH_PLIST = Path.home() / "Library/LaunchAgents" / f"{GROWTH_PLIST_NAME}.plist"

# Source plists (in the project folder, already configured)
SEND_PLIST_SRC = SCRIPT_DIR / f"{SEND_PLIST_NAME}.plist"
GROWTH_PLIST_SRC = SCRIPT_DIR / f"{GROWTH_PLIST_NAME}.plist"

VENV_PYTHON = SCRIPT_DIR / "venv/bin/python"

# How long without activity before we consider a script "dead"
SEND_STALE_HOURS = 2       # Send script should run every hour
GROWTH_STALE_HOURS = 8     # Growth script runs every 6 hours

# Log files to inspect
LOG_FILES = {
    "send": SCRIPT_DIR / "cron_messages.log",
    "growth": SCRIPT_DIR / "cron_growth.log",
    "master": SCRIPT_DIR / "master_automation.log",
}

SESSION_FILES = [
    SCRIPT_DIR / "cron_session.session",
    SCRIPT_DIR / "cron_growth_session.session",
    SCRIPT_DIR / "master_session.session",
    SCRIPT_DIR / "techyera_marketing.session",
]

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(WATCHDOG_LOG),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("watchdog")


# ── Helpers ────────────────────────────────────────────────────────────────────

def run_cmd(cmd, check=False):
    """Run a shell command, return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, "", str(e)


def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)


def load_fail_tracker():
    if FAIL_TRACK_FILE.exists():
        try:
            with open(FAIL_TRACK_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_fail_tracker(tracker):
    with open(FAIL_TRACK_FILE, 'w') as f:
        json.dump(tracker, f, indent=2)


# ── Check 1: launchd service status ───────────────────────────────────────────

def check_launchd_services():
    """Returns dict of service_name -> is_loaded (bool)."""
    rc, stdout, _ = run_cmd(["launchctl", "list"])
    loaded = {}
    for name in [SEND_PLIST_NAME, GROWTH_PLIST_NAME]:
        loaded[name] = name in stdout
    return loaded


def install_plist(src_plist: Path, dest_plist: Path, service_name: str):
    """Copy plist to LaunchAgents and load it."""
    try:
        # Ensure LaunchAgents dir exists
        dest_plist.parent.mkdir(parents=True, exist_ok=True)

        # Copy if source exists and dest is missing/outdated
        if src_plist.exists():
            import shutil
            shutil.copy2(src_plist, dest_plist)
            logger.info(f"Copied {src_plist.name} → {dest_plist}")
        elif not dest_plist.exists():
            logger.error(f"Cannot install {service_name}: plist source not found at {src_plist}")
            return False

        # Unload first (ignore errors)
        run_cmd(["launchctl", "unload", str(dest_plist)])

        # Load
        rc, out, err = run_cmd(["launchctl", "load", str(dest_plist)])
        if rc == 0:
            logger.info(f"✅ Loaded launchd service: {service_name}")
            return True
        else:
            logger.error(f"Failed to load {service_name}: {err.strip()}")
            return False
    except Exception as e:
        logger.error(f"Exception installing {service_name}: {e}")
        return False


def reload_service(service_name: str, plist_dest: Path, plist_src: Path):
    """Unload and reload a launchd service."""
    logger.info(f"Reloading service: {service_name}")
    run_cmd(["launchctl", "unload", str(plist_dest)])
    return install_plist(plist_src, plist_dest, service_name)


# ── Check 2: log freshness ────────────────────────────────────────────────────

def get_last_activity_time(log_path: Path):
    """Scan the log file and return the timestamp of the most recent entry."""
    if not log_path.exists():
        return None

    # Read last 200 lines
    try:
        with open(log_path, 'r', errors='replace') as f:
            lines = f.readlines()
        lines = lines[-200:]
    except Exception:
        return None

    ts_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
    last_ts = None
    for line in reversed(lines):
        m = ts_pattern.match(line)
        if m:
            try:
                last_ts = datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')
                break
            except ValueError:
                continue
    return last_ts


def check_log_freshness():
    """Returns dict with last activity times and staleness flags."""
    now = datetime.now()
    result = {}

    for key, log_path in LOG_FILES.items():
        last = get_last_activity_time(log_path)
        if last is None:
            result[key] = {"last": None, "stale": True, "hours_ago": None}
        else:
            hours_ago = (now - last).total_seconds() / 3600
            stale_threshold = SEND_STALE_HOURS if key == "send" else GROWTH_STALE_HOURS
            result[key] = {
                "last": last.strftime('%Y-%m-%d %H:%M:%S'),
                "hours_ago": round(hours_ago, 1),
                "stale": hours_ago > stale_threshold
            }
    return result


# ── Check 3: stale session journals ───────────────────────────────────────────

def clear_stale_journals():
    """Delete any leftover .session-journal files (cause DB locked errors)."""
    cleared = []
    for session_file in SESSION_FILES:
        journal = Path(str(session_file) + "-journal")
        if journal.exists():
            try:
                journal.unlink()
                cleared.append(journal.name)
                logger.info(f"Cleared stale journal: {journal.name}")
            except Exception as e:
                logger.warning(f"Could not clear {journal.name}: {e}")
    return cleared


# ── Check 4: auto-disable permanently failing targets ─────────────────────────

PERMANENT_ERROR_PATTERNS = [
    r"No permission",
    r"ChatWriteForbidden",
    r"private and you lack perm",
    r"you were banned",
    r"Could not find the input entity",
    r"ChannelPrivateError",
    r"UserBannedInChannel",
]

def analyze_send_log_for_failures():
    """
    Scan the send log for recent per-target errors.
    Returns dict: username_fragment -> error_type
    """
    log_path = LOG_FILES["send"]
    if not log_path.exists():
        return {}

    failures = {}
    try:
        with open(log_path, 'r', errors='replace') as f:
            lines = f.readlines()
        lines = lines[-500:]
    except Exception:
        return {}

    for line in lines:
        # e.g. "No permission: Fresher Jobs & Internships (83K)"
        for pat in PERMANENT_ERROR_PATTERNS:
            if re.search(pat, line, re.IGNORECASE):
                # Try to extract target name after the error type
                m = re.search(r'(?:No permission|Error|Cannot|Banned)[:\s]+(.+)', line, re.IGNORECASE)
                if m:
                    fragment = m.group(1).strip()[:60]
                    failures[fragment] = pat
                break

    return failures


def auto_disable_bad_targets(config, fail_tracker):
    """
    Cross-reference fail_tracker with config targets.
    Disable any target that has 3+ consecutive permanent failures.
    Returns (config, changed: bool, disabled_names: list)
    """
    disabled = []
    changed = False
    MAX_FAILS = 3

    for target in config.get('targets', []):
        uid = target.get('username', '')
        fails = fail_tracker.get(uid, 0)
        if fails >= MAX_FAILS and target.get('enabled', True):
            target['enabled'] = False
            changed = True
            disabled.append(target.get('name', uid))
            logger.warning(f"AUTO-DISABLED: {target.get('name', uid)} (fail count: {fails})")

    return config, changed, disabled


# ── Main watchdog routine ──────────────────────────────────────────────────────

def run_watchdog():
    logger.info("")
    logger.info("=" * 60)
    logger.info("  TELEGRAM WATCHDOG — Daily Health Check")
    logger.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    issues_found = []
    fixes_applied = []

    # ── 1. Clear stale SQLite journals (do this first, always) ────────────────
    logger.info("\n[1/4] Checking for stale SQLite session journals...")
    cleared = clear_stale_journals()
    if cleared:
        fixes_applied.append(f"Cleared {len(cleared)} stale session journal(s): {', '.join(cleared)}")
    else:
        logger.info("  → No stale journals found. ✓")

    # ── 2. Auto-disable permanently failing targets ────────────────────────────
    logger.info("\n[2/4] Checking for permanently failing targets...")
    try:
        config = load_config()
        fail_tracker = load_fail_tracker()
        config, changed, disabled = auto_disable_bad_targets(config, fail_tracker)
        if changed:
            save_config(config)
            fixes_applied.append(f"Auto-disabled {len(disabled)} bad target(s): {', '.join(disabled)}")
        else:
            enabled = sum(1 for t in config.get('targets', []) if t.get('enabled', True))
            total = len(config.get('targets', []))
            logger.info(f"  → Targets OK: {enabled}/{total} enabled. ✓")
    except Exception as e:
        logger.error(f"  → Could not analyze targets: {e}")
        issues_found.append(f"Target analysis error: {e}")

    # ── 3. Check log freshness ─────────────────────────────────────────────────
    logger.info("\n[3/4] Checking log freshness...")
    freshness = check_log_freshness()
    scripts_need_restart = False

    for key, info in freshness.items():
        if info["last"] is None:
            msg = f"  → {key}: NO LOG FILE FOUND — script may never have run"
            logger.warning(msg)
            issues_found.append(msg.strip())
            scripts_need_restart = True
        elif info["stale"]:
            msg = f"  → {key}: STALE — last activity {info['hours_ago']}h ago (limit: {SEND_STALE_HOURS if key == 'send' else GROWTH_STALE_HOURS}h)"
            logger.warning(msg)
            issues_found.append(msg.strip())
            scripts_need_restart = True
        else:
            logger.info(f"  → {key}: OK — last activity {info['hours_ago']}h ago ✓")

    # ── 4. Check & fix launchd services ───────────────────────────────────────
    logger.info("\n[4/4] Checking launchd services...")
    services = check_launchd_services()

    send_ok = services.get(SEND_PLIST_NAME, False)
    growth_ok = services.get(GROWTH_PLIST_NAME, False)

    logger.info(f"  → {SEND_PLIST_NAME}: {'LOADED ✓' if send_ok else '❌ NOT LOADED'}")
    logger.info(f"  → {GROWTH_PLIST_NAME}: {'LOADED ✓' if growth_ok else '❌ NOT LOADED'}")

    need_send_reload = not send_ok or scripts_need_restart
    need_growth_reload = not growth_ok or scripts_need_restart

    if need_send_reload:
        issues_found.append(f"{SEND_PLIST_NAME} is not running or logs are stale")
        logger.info(f"  → Attempting to install/reload {SEND_PLIST_NAME}...")
        ok = install_plist(SEND_PLIST_SRC, SEND_PLIST, SEND_PLIST_NAME)
        if ok:
            fixes_applied.append(f"Reloaded launchd service: {SEND_PLIST_NAME}")
        else:
            issues_found.append(f"Could not reload {SEND_PLIST_NAME} — check plist path")

    if need_growth_reload:
        issues_found.append(f"{GROWTH_PLIST_NAME} is not running or logs are stale")
        logger.info(f"  → Attempting to install/reload {GROWTH_PLIST_NAME}...")
        ok = install_plist(GROWTH_PLIST_SRC, GROWTH_PLIST, GROWTH_PLIST_NAME)
        if ok:
            fixes_applied.append(f"Reloaded launchd service: {GROWTH_PLIST_NAME}")
        else:
            issues_found.append(f"Could not reload {GROWTH_PLIST_NAME} — check plist path")

    # ── Summary ────────────────────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 60)
    logger.info("  WATCHDOG SUMMARY")
    logger.info("=" * 60)

    if not issues_found and not fixes_applied:
        logger.info("  ✅ Everything looks healthy — no action needed.")
    else:
        if issues_found:
            logger.info(f"  ⚠️  Issues detected ({len(issues_found)}):")
            for issue in issues_found:
                logger.info(f"       • {issue}")
        if fixes_applied:
            logger.info(f"  🔧 Fixes applied ({len(fixes_applied)}):")
            for fix in fixes_applied:
                logger.info(f"       • {fix}")

    logger.info("")
    logger.info(f"  Enabled targets: {sum(1 for t in config.get('targets', []) if t.get('enabled', True))}/{len(config.get('targets', []))}")

    # Log file sizes (trim if too large)
    for key, log_path in LOG_FILES.items():
        if log_path.exists():
            size_mb = log_path.stat().st_size / 1024 / 1024
            if size_mb > 10:
                logger.info(f"  ⚠️  {log_path.name} is {size_mb:.1f}MB — trimming to last 5000 lines")
                try:
                    with open(log_path, 'r', errors='replace') as f:
                        lines = f.readlines()
                    with open(log_path, 'w') as f:
                        f.writelines(lines[-5000:])
                except Exception as e:
                    logger.warning(f"  Could not trim {log_path.name}: {e}")

    logger.info("=" * 60)
    logger.info("  Watchdog run complete.")
    logger.info("=" * 60)

    return len(issues_found), len(fixes_applied)


if __name__ == "__main__":
    issues, fixes = run_watchdog()
    # Exit code: 0 = all good or fixed, 1 = unfixed issues remain
    sys.exit(0 if fixes >= issues or issues == 0 else 1)
