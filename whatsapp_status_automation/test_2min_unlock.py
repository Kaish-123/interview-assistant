#!/usr/bin/env python3
"""
Test unlock after 2 minutes (simulates scheduled wake).
Lock your screen immediately after running this!
"""

import subprocess
import time
import sys

PASSWORD = "NewNew@123"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

def unlock_sequence():
    """Wake display and unlock with password."""
    
    # First, wake the display
    log("💡 Waking display with caffeinate...")
    subprocess.Popen(["caffeinate", "-u", "-t", "120"])
    time.sleep(3)
    
    # Now run unlock AppleScript
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

def main():
    log("=" * 50)
    log("🧪 2-MINUTE UNLOCK TEST")
    log("=" * 50)
    log("")
    log("🔒 LOCK YOUR SCREEN NOW!")
    log("   Press: Cmd + Ctrl + Q")
    log("")
    log("   Script will wait 2 minutes, then:")
    log("   1. Wake the display")
    log("   2. Enter password")
    log("   3. Unlock your Mac")
    log("")
    
    # Countdown 2 minutes (120 seconds)
    total_seconds = 120
    
    for remaining in range(total_seconds, 0, -1):
        mins = remaining // 60
        secs = remaining % 60
        print(f"\r   ⏳ Waiting: {mins:02d}:{secs:02d} remaining...   ", end="")
        sys.stdout.flush()
        time.sleep(1)
    
    print()
    log("")
    log("⏰ 2 minutes passed! Starting unlock...")
    log("")
    
    # Try unlock 3 times
    for attempt in range(3):
        log(f"🔓 Unlock attempt {attempt + 1}/3...")
        
        success = unlock_sequence()
        
        time.sleep(5)
        
        # Check if unlocked
        check = subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to return name of first process whose frontmost is true'],
            capture_output=True, text=True
        )
        front_app = check.stdout.strip().lower()
        log(f"   Front app: {front_app}")
        
        if "loginwindow" not in front_app:
            log("✅ SUCCESS! Screen unlocked!")
            return
        
        log("   ⚠️ Still locked, retrying...")
        time.sleep(2)
    
    log("❌ Could not unlock after 3 attempts")

if __name__ == "__main__":
    main()

