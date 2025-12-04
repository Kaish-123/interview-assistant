#!/usr/bin/env python3
"""
WhatsApp Status Automation for macOS
====================================
Automatically sets your WhatsApp Status (Stories) on weekends.

This sets the WhatsApp STATUS feature (like Instagram Stories),
NOT a chat message.

Author: Auto-generated
"""

import json
import os
import subprocess
import time
import sys
from datetime import datetime
from pathlib import Path

try:
    import pyautogui
except ImportError:
    print("❌ pyautogui not installed. Run: pip install pyautogui")
    sys.exit(1)

# Safety settings
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.3


class WhatsAppStatusAutomation:
    """Automates WhatsApp Status (Stories) updates on macOS."""
    
    def __init__(self, config_path: str = None):
        """Initialize with config file."""
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "config.json"
        )
        self.config = self.load_config()
        self.delay = self.config.get("delay_between_actions", 1.5)
    
    def load_config(self) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Config not found at {self.config_path}, using defaults")
            return {
                "status_captions": ["Weekend vibes ✨"],
                "schedule": {"days": ["saturday", "sunday"], "time": "09:00"},
                "whatsapp_app_name": "WhatsApp",
                "delay_between_actions": 1.5,
                "use_random_caption": False,
                "current_caption_index": 0
            }
    
    def save_config(self):
        """Save current config to file."""
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)
    
    def get_caption(self) -> str:
        """Get the caption to use for status."""
        captions = self.config.get("status_captions", ["Weekend mode 🌴"])
        
        if self.config.get("use_random_caption", False):
            import random
            return random.choice(captions)
        else:
            idx = self.config.get("current_caption_index", 0) % len(captions)
            return captions[idx]
    
    def rotate_caption(self):
        """Move to next caption in the list."""
        captions = self.config.get("status_captions", [])
        if captions:
            self.config["current_caption_index"] = (
                self.config.get("current_caption_index", 0) + 1
            ) % len(captions)
            self.save_config()
    
    def is_whatsapp_running(self) -> bool:
        """Check if WhatsApp is currently running."""
        try:
            result = subprocess.run(
                ["pgrep", "-x", "WhatsApp"],
                capture_output=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def open_whatsapp(self) -> bool:
        """Open WhatsApp application and ensure it's ready."""
        app_name = self.config.get("whatsapp_app_name", "WhatsApp")
        
        was_running = self.is_whatsapp_running()
        print(f"📱 Opening {app_name}... (was {'running' if was_running else 'closed'})")
        
        # Use 'open' command which is more reliable for launching apps
        try:
            subprocess.run(["open", "-a", app_name], check=True)
        except subprocess.CalledProcessError:
            print(f"❌ Failed to open {app_name}")
            return False
        
        # Wait for app to fully open
        if not was_running:
            print("   Waiting for app to start...")
            time.sleep(3)  # Give it more time if it wasn't running
        else:
            time.sleep(1)
        
        # Activate and bring to front
        script = f'''
        tell application "{app_name}"
            activate
        end tell
        delay 1
        tell application "System Events"
            set frontmost of process "{app_name}" to true
        end tell
        '''
        
        try:
            subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
            time.sleep(self.delay)
            print("   ✅ WhatsApp is now active")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️ Activation warning: {e}")
            time.sleep(2)
            return True  # Continue anyway
    
    def click_status_tab(self) -> bool:
        """
        Click on the Status tab in WhatsApp sidebar.
        
        WhatsApp Desktop layout:
        - Left sidebar has icons: Chats, Status, Channels, Communities
        - Status is typically the 2nd icon (circle with dashed outline)
        """
        print("📍 Clicking Status tab in sidebar...")
        
        # First, let's make sure we're on WhatsApp
        pyautogui.hotkey('command', '1')  # Try keyboard shortcut
        time.sleep(0.5)
        
        # Get WhatsApp window bounds using AppleScript
        app_name = self.config.get("whatsapp_app_name", "WhatsApp")
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                if exists window 1 then
                    set win to window 1
                    set winPos to position of win
                    set winSize to size of win
                    return (item 1 of winPos as string) & "," & (item 2 of winPos as string) & "," & (item 1 of winSize as string) & "," & (item 2 of winSize as string)
                end if
            end tell
        end tell
        '''
        
        window_x, window_y, window_w, window_h = 0, 0, 800, 600
        
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(",")
                window_x, window_y, window_w, window_h = [int(float(p)) for p in parts]
                print(f"   Window at: ({window_x}, {window_y}) size: {window_w}x{window_h}")
        except Exception as e:
            print(f"   ⚠️ Could not get window position: {e}")
            # Use default screen position
            screen_w, screen_h = pyautogui.size()
            window_x, window_y = 100, 50
            window_w, window_h = screen_w // 2, screen_h - 100
        
        # WhatsApp sidebar is on the left
        # Status icon is typically the 2nd icon from top in the sidebar
        # Sidebar is about 70px wide, icons are spaced ~50px apart vertically
        
        # Click on Status tab (2nd icon in sidebar)
        # Position: about 35px from left edge, 120-150px from top
        status_x = window_x + 35
        status_y = window_y + 140  # Adjust this if needed
        
        print(f"   Clicking Status tab at ({status_x}, {status_y})...")
        pyautogui.click(status_x, status_y)
        time.sleep(self.delay)
        
        return True
    
    def click_add_status(self) -> bool:
        """
        Click the button to add a new text status.
        
        In WhatsApp Status view:
        - There's a "+" or pencil icon to add new status
        - Or "My status" area to click
        """
        print("➕ Looking for 'Add Status' button...")
        
        # After clicking Status tab, we need to find the "add" button
        # This is usually a "+" icon or pencil icon
        
        # Try keyboard shortcut first (if any)
        # Or click in the status area
        
        # Get window position again
        app_name = self.config.get("whatsapp_app_name", "WhatsApp")
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                if exists window 1 then
                    set win to window 1
                    set winPos to position of win
                    set winSize to size of win
                    return (item 1 of winPos as string) & "," & (item 2 of winPos as string) & "," & (item 1 of winSize as string) & "," & (item 2 of winSize as string)
                end if
            end tell
        end tell
        '''
        
        window_x, window_y, window_w, window_h = 100, 50, 800, 600
        
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(",")
                window_x, window_y, window_w, window_h = [int(float(p)) for p in parts]
        except Exception:
            pass
        
        # The "Add status" or "My status" button is usually:
        # - In the main content area (right of sidebar)
        # - Near the top, around 100-150px from top
        # - About 150-250px from left (past the sidebar)
        
        # Click on "My status" or the text status button
        # Try clicking the pencil/text icon for text status
        add_x = window_x + 200  # Past the sidebar
        add_y = window_y + 130  # Near top of content area
        
        print(f"   Clicking 'Add Status' area at ({add_x}, {add_y})...")
        pyautogui.click(add_x, add_y)
        time.sleep(self.delay)
        
        # Also try clicking a bit more to the right where the pencil icon might be
        # The text status (pencil) icon is often on the right side
        pencil_x = window_x + window_w - 100  # Near right side
        pencil_y = window_y + 130
        
        print(f"   Also trying pencil icon area at ({pencil_x}, {pencil_y})...")
        time.sleep(0.5)
        pyautogui.click(pencil_x, pencil_y)
        time.sleep(self.delay)
        
        return True
    
    def type_status_text(self, caption: str) -> bool:
        """Type the status text and post it."""
        print(f"✏️ Typing status: {caption}")
        
        time.sleep(0.5)
        
        # The text input should now be focused
        # Type the caption using clipboard (for emoji support)
        self._type_unicode(caption)
        
        time.sleep(self.delay)
        
        # Send/Post the status
        # Usually Enter or clicking a send button
        print("   Posting status...")
        
        # Try pressing Enter to send
        pyautogui.press('enter')
        time.sleep(1)
        
        # Or try Cmd+Enter
        pyautogui.hotkey('command', 'enter')
        time.sleep(0.5)
        
        print("   ✅ Status text entered!")
        return True
    
    def _type_unicode(self, text: str):
        """Type unicode text using clipboard (for emojis)."""
        # Copy to clipboard
        process = subprocess.Popen(
            ['pbcopy'],
            stdin=subprocess.PIPE,
            env={'LANG': 'en_US.UTF-8'}
        )
        process.communicate(text.encode('utf-8'))
        
        time.sleep(0.3)
        
        # Paste from clipboard
        pyautogui.hotkey('command', 'v')
        time.sleep(0.3)
    
    def set_status(self, caption: str = None) -> bool:
        """
        Main method: Set WhatsApp Status (Stories) with caption.
        
        Steps:
        1. Open WhatsApp
        2. Click Status tab
        3. Click Add Status / Text Status
        4. Type caption and post
        """
        caption = caption or self.get_caption()
        
        print("\n" + "="*50)
        print("🚀 WhatsApp Status Automation")
        print(f"   Caption: {caption}")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50 + "\n")
        
        # Step 1: Open WhatsApp
        if not self.open_whatsapp():
            print("❌ Failed to open WhatsApp")
            return False
        
        # Step 2: Click Status tab
        if not self.click_status_tab():
            print("⚠️ Status tab click might have failed...")
        
        time.sleep(1)
        
        # Step 3: Click Add Status button
        if not self.click_add_status():
            print("⚠️ Add status click might have failed...")
        
        time.sleep(1)
        
        # Step 4: Type and post status
        if not self.type_status_text(caption):
            print("❌ Failed to type status")
            return False
        
        # Rotate to next caption for next time
        if not self.config.get("use_random_caption", False):
            self.rotate_caption()
        
        print("\n✅ Status update complete!")
        print("\n⚠️ NOTE: Please verify the status was posted correctly.")
        print("   The automation clicks on approximate positions.")
        print("   You may need to adjust coordinates for your screen.")
        return True
    
    def interactive_calibrate(self):
        """Interactive mode to find correct click positions."""
        print("\n🔧 CALIBRATION MODE")
        print("="*50)
        print("This will help you find the correct click positions.")
        print("Move your mouse to each position and note the coordinates.\n")
        
        # Open WhatsApp first
        self.open_whatsapp()
        time.sleep(2)
        
        print("Tracking mouse position for 30 seconds...")
        print("Move mouse to: Status tab, Add Status button, etc.")
        print("Press Ctrl+C to stop.\n")
        
        try:
            for _ in range(60):
                x, y = pyautogui.position()
                print(f"\rMouse position: ({x}, {y})    ", end="", flush=True)
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n\n📝 Use these coordinates to adjust the click positions in the code.")
    
    def is_weekend(self) -> bool:
        """Check if today is a scheduled day."""
        days = self.config.get("schedule", {}).get("days", ["saturday", "sunday"])
        today = datetime.now().strftime("%A").lower()
        return today in [d.lower() for d in days]
    
    def should_run_now(self) -> bool:
        """Check if automation should run based on schedule."""
        if not self.is_weekend():
            return False
        
        scheduled_time = self.config.get("schedule", {}).get("time", "09:00")
        scheduled_hour, scheduled_min = map(int, scheduled_time.split(":"))
        current_hour, current_min = datetime.now().hour, datetime.now().minute
        
        scheduled_minutes = scheduled_hour * 60 + scheduled_min
        current_minutes = current_hour * 60 + current_min
        
        return abs(current_minutes - scheduled_minutes) <= 5


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="WhatsApp Status (Stories) Automation for macOS"
    )
    parser.add_argument(
        "--run", "-r",
        action="store_true",
        help="Run the status update immediately"
    )
    parser.add_argument(
        "--caption", "-c",
        type=str,
        help="Custom caption to use"
    )
    parser.add_argument(
        "--schedule", "-s",
        action="store_true",
        help="Run only if it's the scheduled day/time"
    )
    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Run as daemon (keeps checking schedule)"
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Test mode - print what would happen"
    )
    parser.add_argument(
        "--calibrate",
        action="store_true",
        help="Calibration mode - track mouse position to find correct coordinates"
    )
    
    args = parser.parse_args()
    
    automation = WhatsAppStatusAutomation()
    
    if args.calibrate:
        automation.interactive_calibrate()
        return
    
    if args.test:
        print("🧪 TEST MODE")
        print(f"   Is scheduled day: {automation.is_weekend()}")
        print(f"   Should run now: {automation.should_run_now()}")
        print(f"   Caption would be: {automation.get_caption()}")
        print(f"\n   Scheduled days: {automation.config.get('schedule', {}).get('days', [])}")
        print(f"   Scheduled time: {automation.config.get('schedule', {}).get('time', '09:00')}")
        return
    
    if args.daemon:
        print("🔄 Running in daemon mode...")
        print("   Press Ctrl+C to stop\n")
        
        try:
            import schedule as sched_lib
            
            scheduled_time = automation.config.get("schedule", {}).get("time", "09:00")
            days = automation.config.get("schedule", {}).get("days", ["saturday", "sunday"])
            
            def job():
                if automation.is_weekend():
                    automation.set_status(args.caption)
            
            for day in days:
                getattr(sched_lib.every(), day).at(scheduled_time).do(job)
            
            print(f"   Scheduled for: {', '.join(days)} at {scheduled_time}")
            
            while True:
                sched_lib.run_pending()
                time.sleep(60)
                
        except KeyboardInterrupt:
            print("\n👋 Daemon stopped")
            return
    
    if args.schedule:
        if automation.should_run_now():
            print("✅ Schedule matches - running status update")
            automation.set_status(args.caption)
        else:
            print("⏳ Not scheduled time, skipping")
            print(f"   Today: {datetime.now().strftime('%A')}")
            print(f"   Scheduled: {automation.config.get('schedule', {}).get('days', [])}")
        return
    
    if args.run or args.caption:
        automation.set_status(args.caption)
        return
    
    # Default: show help
    parser.print_help()
    print("\n💡 Quick start:")
    print("   ./run.sh --run              # Run now")
    print("   ./run.sh --calibrate        # Find correct click positions")
    print("   ./run.sh --test             # Test what would happen")


if __name__ == "__main__":
    main()
