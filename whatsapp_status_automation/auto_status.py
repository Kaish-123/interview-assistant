#!/usr/bin/env python3
"""
WhatsApp Auto Status - Full Automation
Wake → Unlock → Post All Images
"""

import subprocess
import time
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PASSWORD = "NewNew@123"

def log(msg):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")
    sys.stdout.flush()

def is_screen_locked():
    """Check if login screen is showing."""
    result = subprocess.run(
        ["osascript", "-e", 'tell application "System Events" to return name of first process whose frontmost is true'],
        capture_output=True, text=True
    )
    front_app = result.stdout.strip().lower()
    log(f"   Front app: {front_app}")
    return "loginwindow" in front_app

def aggressive_wake():
    """Wake the display aggressively - multiple methods."""
    log("💡 Aggressively waking display...")
    
    # Method 1: caffeinate (multiple times)
    subprocess.Popen(["caffeinate", "-u", "-t", "300"])
    time.sleep(1)
    subprocess.run(["caffeinate", "-u", "-t", "5"], capture_output=True)
    time.sleep(1)
    subprocess.run(["caffeinate", "-u", "-t", "5"], capture_output=True)
    time.sleep(2)
    
    log("   ✅ Wake signals sent")

def unlock_sequence():
    """Fast unlock sequence with optimized timing."""
    
    # Wake the display
    log("💡 Waking display...")
    subprocess.Popen(["caffeinate", "-u", "-t", "120"])
    time.sleep(2)
    
    # FAST unlock AppleScript with your timing
    script = f'''
    tell application "System Events"
        -- Wake screen
        key code 49 -- Space
        delay 1.5 -- Wait 1.5 sec after wake
        
        -- Enter to show password field
        key code 36
        delay 1 -- Wait 1 sec for password field
        
        -- Type password
        keystroke "{PASSWORD}"
        delay 0.5
        
        -- Submit
        key code 36 -- Enter
    end tell
    '''
    
    log("🔑 Entering password...")
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    
    if result.stderr:
        log(f"   Error: {result.stderr}")
    
    # Wait 2 seconds after submit
    time.sleep(2)
    
    return result.returncode == 0

def unlock_if_needed():
    """Only unlock if screen is locked."""
    log("🔍 Checking if unlock needed...")
    
    # Aggressive wake first
    aggressive_wake()
    time.sleep(2)
    
    if not is_screen_locked():
        log("   ✅ Already unlocked!")
        return True
    
    log("   Screen is locked, unlocking...")
    
    # Try unlock 3 times
    for attempt in range(3):
        log(f"   Attempt {attempt + 1}/3...")
        
        # Extra wake before each attempt
        subprocess.run(["caffeinate", "-u", "-t", "10"], capture_output=True)
        time.sleep(2)
        
        unlock_sequence()
        time.sleep(5)
        
        if not is_screen_locked():
            log("   ✅ Successfully unlocked!")
            return True
        
        log("   ⚠️ Still locked, retrying...")
        time.sleep(2)
    
    log("   ❌ Could not unlock")
    return False

def run_whatsapp_status():
    """Run WhatsApp status automation."""
    log("🚀 Starting WhatsApp status automation...")
    
    script_path = os.path.join(SCRIPT_DIR, "whatsapp_status.py")
    venv_python = os.path.join(SCRIPT_DIR, "venv", "bin", "python")
    python_cmd = venv_python if os.path.exists(venv_python) else sys.executable
    
    result = subprocess.run(
        [python_cmd, script_path, "--all"],
        capture_output=True,
        text=True,
        cwd=SCRIPT_DIR
    )
    
    log("Output:")
    print(result.stdout)
    if result.stderr:
        log("Errors:")
        print(result.stderr)

def main():
    log("")
    log("=" * 60)
    log("🕕 WhatsApp Auto Status - Scheduled Run")
    log("=" * 60)
    log("")
    
    # Step 1: Unlock if needed
    unlocked = unlock_if_needed()
    
    if not unlocked:
        log("⚠️ Unlock failed, trying to continue anyway...")
    
    # Step 2: Wait for desktop
    log("⏳ Waiting 5 seconds for desktop...")
    time.sleep(5)
    
    # Step 3: Post WhatsApp status
    run_whatsapp_status()
    
    log("")
    log("✅ Complete!")

if __name__ == "__main__":
    main()
