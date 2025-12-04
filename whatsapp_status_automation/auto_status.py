#!/usr/bin/env python3
"""
WhatsApp Auto Status - Full Automation
Wake → Click to activate → Enter password → Post status
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
    """
    Wake and unlock with CLICKS + KEY PRESSES.
    Based on user feedback:
    - Screen wakes but Enter doesn't work
    - Need to CLICK to activate the login window first
    """
    
    # Step 1: Wake display aggressively
    log("💡 Step 1: Waking display...")
    subprocess.Popen(["caffeinate", "-u", "-t", "120"])
    time.sleep(2)
    subprocess.run(["caffeinate", "-u", "-t", "5"], capture_output=True)
    time.sleep(2)
    
    # Step 2: Use pyautogui to CLICK center of screen (activates login window)
    log("🖱️ Step 2: Clicking to activate login window...")
    try:
        import pyautogui
        screen_w, screen_h = pyautogui.size()
        center_x, center_y = screen_w // 2, screen_h // 2
        
        # Click center of screen
        pyautogui.click(center_x, center_y)
        time.sleep(1)
        pyautogui.click(center_x, center_y)
        time.sleep(2)
        
        log(f"   Clicked at ({center_x}, {center_y})")
    except Exception as e:
        log(f"   Click failed: {e}, using AppleScript...")
        # Fallback: press Space to wake
        subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 49'], capture_output=True)
        time.sleep(2)
    
    # Step 3: Press Enter to show password field
    log("⌨️ Step 3: Pressing Enter to show password field...")
    script_enter = '''
    tell application "System Events"
        key code 36 -- Enter
    end tell
    '''
    subprocess.run(["osascript", "-e", script_enter], capture_output=True)
    time.sleep(2)
    
    # Step 4: Type password and submit
    log("🔑 Step 4: Typing password...")
    script_password = f'''
    tell application "System Events"
        keystroke "{PASSWORD}"
        delay 1
        key code 36 -- Enter
    end tell
    '''
    subprocess.run(["osascript", "-e", script_password], capture_output=True)
    
    log("   ✅ Unlock sequence sent")
    return True

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
    
    # Try unlock up to 3 times
    for attempt in range(3):
        log(f"🔓 Unlock attempt {attempt + 1}/3...")
        
        unlock_sequence()
        time.sleep(5)
        
        if not is_screen_locked():
            log("   ✅ Successfully unlocked!")
            break
        
        log("   ⚠️ Still locked, retrying...")
        time.sleep(2)
    
    # Wait for desktop
    log("⏳ Waiting 5 seconds for desktop...")
    time.sleep(5)
    
    # Post WhatsApp status
    run_whatsapp_status()
    
    log("")
    log("✅ Complete!")

if __name__ == "__main__":
    main()
