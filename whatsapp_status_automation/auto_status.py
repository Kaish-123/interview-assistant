#!/usr/bin/env python3
"""
WhatsApp Auto Status - Runs even with lid closed
Handles: Wake → Unlock → Post Status
"""

import subprocess
import time
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PASSWORD = "NewNew@123"  # Your Mac password

def log(message):
    """Print with timestamp."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def wake_system():
    """Wake up the Mac completely."""
    log("💡 Waking up the system...")
    
    # Method 1: caffeinate to prevent sleep and wake display
    subprocess.run(["caffeinate", "-u", "-t", "10"], capture_output=True)
    time.sleep(2)
    
    # Method 2: Use pmset to wake display
    subprocess.run(["pmset", "displaysleepnow"], capture_output=True)
    time.sleep(1)
    
    # Method 3: Simulate user activity with mouse movement
    try:
        import pyautogui
        # Move mouse slightly to wake display
        x, y = pyautogui.position()
        pyautogui.moveTo(x + 1, y + 1)
        pyautogui.moveTo(x, y)
    except:
        pass
    
    log("   ✅ System wake signal sent")
    time.sleep(3)

def is_screen_locked():
    """Check if the screen is locked."""
    # Method 1: Check for loginwindow process
    result = subprocess.run(
        ["pgrep", "-x", "loginwindow"],
        capture_output=True
    )
    
    # Method 2: Check via AppleScript
    check_script = '''
    tell application "System Events"
        try
            set frontApp to name of first process whose frontmost is true
            if frontApp is "loginwindow" then
                return "locked"
            else
                return "unlocked"
            end if
        on error
            return "locked"
        end try
    end tell
    '''
    result = subprocess.run(["osascript", "-e", check_script], capture_output=True, text=True)
    return "locked" in result.stdout.lower() or "loginwindow" in result.stdout.lower()

def activate_login_screen():
    """Click/press to activate the password field on login screen."""
    log("🖱️ Activating login screen...")
    
    try:
        import pyautogui
        
        # Get screen size
        screen_w, screen_h = pyautogui.size()
        center_x = screen_w // 2
        center_y = screen_h // 2
        
        # Click in center of screen to activate login window
        log(f"   Clicking center of screen ({center_x}, {center_y})...")
        pyautogui.click(center_x, center_y)
        time.sleep(1)
        
        # Click again lower (where password field usually is)
        password_y = center_y + 50
        log(f"   Clicking password area ({center_x}, {password_y})...")
        pyautogui.click(center_x, password_y)
        time.sleep(1)
        
        # Press Space or Enter to ensure field is focused
        pyautogui.press('space')
        time.sleep(0.5)
        
        # Press Escape first to clear any dialogs, then click again
        pyautogui.press('escape')
        time.sleep(0.5)
        pyautogui.click(center_x, password_y)
        time.sleep(1)
        
    except Exception as e:
        log(f"   ⚠️ Click failed: {e}")
        # Fallback: Use AppleScript to press keys
        subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 49'], capture_output=True)  # Space
        time.sleep(1)
    
    log("   ✅ Login screen activated")

def type_password():
    """Type the password to unlock."""
    log(f"🔑 Typing password...")
    
    try:
        import pyautogui
        
        # Clear any existing text first
        pyautogui.hotkey('command', 'a')
        time.sleep(0.2)
        
        # Type password character by character (more reliable)
        for char in PASSWORD:
            pyautogui.press(char)
            time.sleep(0.05)
        
        time.sleep(0.5)
        
        # Press Enter to submit
        log("   Pressing Enter...")
        pyautogui.press('return')
        
    except Exception as e:
        log(f"   ⚠️ pyautogui failed: {e}, using AppleScript...")
        # Fallback: AppleScript
        unlock_script = f'''
        tell application "System Events"
            keystroke "{PASSWORD}"
            delay 0.5
            keystroke return
        end tell
        '''
        subprocess.run(["osascript", "-e", unlock_script], capture_output=True)
    
    log("   ✅ Password entered")
    time.sleep(5)  # Wait for unlock animation

def unlock_screen():
    """Full unlock sequence."""
    log("🔓 Starting unlock sequence...")
    
    # Step 1: Wake the system
    wake_system()
    
    # Step 2: Check if locked
    log("   Checking lock status...")
    
    # Always try to unlock (safer)
    for attempt in range(3):
        log(f"   Unlock attempt {attempt + 1}/3...")
        
        # Activate the login screen
        activate_login_screen()
        time.sleep(1)
        
        # Type password
        type_password()
        time.sleep(3)
        
        # Check if unlocked
        if not is_screen_locked():
            log("   ✅ Screen unlocked successfully!")
            return True
        
        log("   ⚠️ Still locked, retrying...")
        time.sleep(2)
    
    log("   ⚠️ Could not confirm unlock, continuing anyway...")
    return False

def run_status_automation():
    """Run the WhatsApp status automation."""
    log("🚀 Running WhatsApp status automation...")
    
    # Run the main script with --all to post all images
    script_path = os.path.join(SCRIPT_DIR, "whatsapp_status.py")
    venv_python = os.path.join(SCRIPT_DIR, "venv", "bin", "python")
    
    # Use venv python if available
    python_cmd = venv_python if os.path.exists(venv_python) else sys.executable
    
    result = subprocess.run(
        [python_cmd, script_path, "--all"],
        capture_output=True,
        text=True,
        cwd=SCRIPT_DIR
    )
    
    log("Output from status script:")
    print(result.stdout)
    if result.stderr:
        log("Errors:")
        print(result.stderr)

def main():
    """Main entry point for scheduled execution."""
    log("")
    log("=" * 60)
    log("🕕 WhatsApp Auto Status - Scheduled Run")
    log("=" * 60)
    log("")
    
    # Step 1: Wake and unlock
    unlock_screen()
    
    # Step 2: Wait for desktop to be fully ready
    log("⏳ Waiting for desktop to be ready (10 seconds)...")
    time.sleep(10)
    
    # Step 3: Run the status automation
    run_status_automation()
    
    log("")
    log("✅ Auto status complete!")

if __name__ == "__main__":
    main()
