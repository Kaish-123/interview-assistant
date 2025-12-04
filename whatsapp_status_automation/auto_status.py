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

def unlock_screen():
    """Unlock the Mac screen with password."""
    print("🔓 Checking if screen needs unlocking...")
    
    # Check if screen is locked
    check_script = '''
    tell application "System Events"
        try
            set isLocked to (name of first process whose frontmost is true) is "loginwindow"
        on error
            set isLocked to false
        end try
        return isLocked
    end tell
    '''
    
    result = subprocess.run(["osascript", "-e", check_script], capture_output=True, text=True)
    is_locked = "true" in result.stdout.lower()
    
    if is_locked:
        print("   Screen is locked, unlocking...")
        
        # Wake the screen first
        subprocess.run(["caffeinate", "-u", "-t", "2"])
        time.sleep(2)
        
        # Type password and press enter
        unlock_script = f'''
        tell application "System Events"
            keystroke "{PASSWORD}"
            delay 0.5
            keystroke return
        end tell
        '''
        subprocess.run(["osascript", "-e", unlock_script], capture_output=True)
        time.sleep(5)
        print("   ✅ Screen unlocked!")
    else:
        print("   ✅ Screen already unlocked")

def wake_display():
    """Wake up the display."""
    print("💡 Waking display...")
    subprocess.run(["caffeinate", "-u", "-t", "5"])
    time.sleep(3)
    print("   ✅ Display awake")

def run_status_automation():
    """Run the WhatsApp status automation."""
    print("🚀 Running WhatsApp status automation...")
    
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
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)

def main():
    """Main entry point for scheduled execution."""
    print("\n" + "="*60)
    print("🕕 WhatsApp Auto Status - Scheduled Run")
    print("="*60 + "\n")
    
    # Step 1: Wake display
    wake_display()
    
    # Step 2: Unlock screen if needed
    unlock_screen()
    
    # Step 3: Wait for desktop to be ready
    print("⏳ Waiting for desktop to be ready...")
    time.sleep(5)
    
    # Step 4: Run the status automation
    run_status_automation()
    
    print("\n✅ Auto status complete!")

if __name__ == "__main__":
    main()

