#!/usr/bin/env python3
"""
WhatsApp Auto Status - Full Automation
Uses the EXACT working unlock sequence from test_2min_unlock.py
"""

import subprocess
import time
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PASSWORD = "NewNew@123"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

def unlock_sequence():
    """EXACT COPY from working test_2min_unlock.py"""
    
    # First, wake the display
    log("💡 Waking display with caffeinate...")
    subprocess.Popen(["caffeinate", "-u", "-t", "120"])
    time.sleep(3)
    
    # THE WORKING AppleScript from test_2min_unlock.py
    script = f'''
    tell application "System Events"
        -- Wake the screen
        key code 49 -- Space
        delay 2
        
        -- First Enter - dismiss wake screen
        key code 36
        delay 2
        
        -- Second Enter - focus password field  
        key code 36
        delay 5 -- Wait 5 seconds for password field to be ready
        
        -- Type password
        keystroke "{PASSWORD}"
        delay 1
        
        -- Submit
        key code 36 -- Enter
    end tell
    '''
    
    log("🔑 Sending unlock sequence...")
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    
    if result.stderr:
        log(f"   Error: {result.stderr}")
    
    return result.returncode == 0

def is_screen_locked():
    """Check if login screen is showing."""
    result = subprocess.run(
        ["osascript", "-e", 'tell application "System Events" to return name of first process whose frontmost is true'],
        capture_output=True, text=True
    )
    front_app = result.stdout.strip().lower()
    log(f"   Front app: {front_app}")
    return "loginwindow" in front_app

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
    
    # Step 1: Try unlock (same as test_2min_unlock.py)
    log("🔓 Starting unlock sequence...")
    
    for attempt in range(3):
        log(f"   Attempt {attempt + 1}/3...")
        
        unlock_sequence()
        time.sleep(5)
        
        # Check if unlocked
        if not is_screen_locked():
            log("   ✅ Successfully unlocked!")
            break
        
        log("   ⚠️ Still locked, retrying...")
        time.sleep(2)
    
    # Step 2: Wait for desktop
    log("⏳ Waiting 5 seconds for desktop...")
    time.sleep(5)
    
    # Step 3: Post WhatsApp status
    run_whatsapp_status()
    
    log("")
    log("✅ Complete!")

if __name__ == "__main__":
    main()
