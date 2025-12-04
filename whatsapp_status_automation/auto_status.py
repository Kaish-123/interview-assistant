#!/usr/bin/env python3
"""
WhatsApp Auto Status - Wake, Unlock, Post
Uses AppleScript for reliable login screen interaction
"""

import subprocess
import time
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PASSWORD = "NewNew@123"

def log(message):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()

def run_applescript(script):
    """Run AppleScript and return result."""
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True
    )
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()

def is_screen_locked():
    """Check if login screen is showing."""
    script = '''
    tell application "System Events"
        set frontApp to name of first process whose frontmost is true
        return frontApp
    end tell
    '''
    success, output, _ = run_applescript(script)
    log(f"   Front app: {output}")
    return "loginwindow" in output.lower()

def wake_and_unlock():
    """
    Wake Mac and unlock using AppleScript only.
    This is more reliable than pyautogui for login screen.
    """
    log("🔓 Starting wake and unlock sequence...")
    
    # Step 1: Wake the display using caffeinate
    log("   Step 1: Waking display...")
    subprocess.Popen(["caffeinate", "-u", "-t", "120"])  # Keep awake for 2 min
    time.sleep(2)
    
    # Step 2: Check if already unlocked
    if not is_screen_locked():
        log("   ✅ Already unlocked!")
        return True
    
    # Step 3: Unlock sequence using AppleScript
    log("   Step 2: Sending unlock sequence...")
    
    # The unlock AppleScript:
    # - Press keys to wake login screen
    # - Wait for password field
    # - Type password
    # - Press Enter
    unlock_script = f'''
    tell application "System Events"
        -- Wake up the screen
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
        
        -- Press Enter to submit
        key code 36
    end tell
    '''
    
    for attempt in range(3):
        log(f"   Attempt {attempt + 1}/3...")
        
        # Keep display awake
        subprocess.run(["caffeinate", "-u", "-t", "10"], capture_output=True)
        time.sleep(1)
        
        # Run unlock script
        success, output, error = run_applescript(unlock_script)
        
        if error:
            log(f"   AppleScript error: {error}")
        
        # Wait for unlock
        time.sleep(5)
        
        # Check if unlocked
        if not is_screen_locked():
            log("   ✅ Successfully unlocked!")
            return True
        
        log("   ⚠️ Still locked, trying again...")
        time.sleep(2)
    
    log("   ❌ Could not unlock after 3 attempts")
    return False

def unlock_only_if_needed():
    """Only run unlock if display is off or screen is locked."""
    log("🔍 Checking system state...")
    
    # Start keeping system awake
    subprocess.Popen(["caffeinate", "-u", "-t", "300"], stdout=subprocess.DEVNULL)
    
    # Check if screen is locked
    if is_screen_locked():
        log("   Screen is locked, need to unlock")
        return wake_and_unlock()
    else:
        log("   ✅ Screen already unlocked, skipping unlock")
        return True

def run_whatsapp_status():
    """Run the WhatsApp status script."""
    log("🚀 Running WhatsApp status automation...")
    
    script_path = os.path.join(SCRIPT_DIR, "whatsapp_status.py")
    venv_python = os.path.join(SCRIPT_DIR, "venv", "bin", "python")
    python_cmd = venv_python if os.path.exists(venv_python) else sys.executable
    
    result = subprocess.run(
        [python_cmd, script_path, "--all"],
        capture_output=True,
        text=True,
        cwd=SCRIPT_DIR
    )
    
    log("Output from WhatsApp script:")
    print(result.stdout)
    if result.stderr:
        log("Errors:")
        print(result.stderr)

def main():
    log("")
    log("=" * 60)
    log("🕕 WhatsApp Auto Status")
    log("=" * 60)
    log("")
    
    # Step 1: Unlock if needed
    unlocked = unlock_only_if_needed()
    
    if not unlocked:
        log("⚠️ Unlock failed, trying to continue anyway...")
    
    # Step 2: Wait for desktop to be ready
    log("⏳ Waiting 5 seconds for desktop...")
    time.sleep(5)
    
    # Step 3: Run WhatsApp status
    run_whatsapp_status()
    
    log("")
    log("✅ Complete!")

if __name__ == "__main__":
    main()
