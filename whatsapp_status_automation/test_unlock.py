#!/usr/bin/env python3
"""
Test ONLY the unlock functionality.
Run this, then QUICKLY lock your screen (Cmd+Ctrl+Q) to test.
"""

import subprocess
import time
import sys

PASSWORD = "NewNew@123"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

def unlock_with_applescript():
    """Unlock using AppleScript - most reliable method."""
    
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
        delay 5 -- IMPORTANT: Wait 5 seconds for password field to be ready
        
        -- Type password
        keystroke "{PASSWORD}"
        delay 1
        
        -- Submit
        key code 36 -- Enter
    end tell
    '''
    
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.returncode == 0, result.stderr

def main():
    log("=" * 50)
    log("🧪 UNLOCK TEST")
    log("=" * 50)
    log("")
    log("⚠️  You have 5 seconds to LOCK your screen!")
    log("    Press: Cmd + Ctrl + Q")
    log("")
    
    for i in range(5, 0, -1):
        log(f"   {i}...")
        time.sleep(1)
    
    log("")
    log("🔓 Starting unlock sequence...")
    log("")
    
    # Keep display awake
    subprocess.Popen(["caffeinate", "-u", "-t", "60"])
    time.sleep(2)
    
    # Try to unlock
    log("   Sending: Space (wake)")
    log("   Sending: Enter (dismiss)")
    log("   Sending: Enter (focus)")
    log("   Sending: Space (ensure)")
    log("   Typing: password")
    log("   Sending: Enter (submit)")
    log("")
    
    success, error = unlock_with_applescript()
    
    if error:
        log(f"   Error: {error}")
    
    time.sleep(3)
    log("")
    log("✅ Unlock sequence complete!")
    log("   Check if your Mac is unlocked now.")

if __name__ == "__main__":
    main()

