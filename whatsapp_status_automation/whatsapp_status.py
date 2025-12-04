#!/usr/bin/env python3
"""
WhatsApp Status Automation for macOS
====================================
Automatically sets your WhatsApp status on weekends (Saturday & Sunday).

Features:
- Opens WhatsApp app on Mac
- Navigates to status settings
- Sets your custom caption
- Runs on schedule (weekends)

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

# Disable pyautogui fail-safe for smoother automation (move mouse to corner to abort)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5  # Add small pause between actions


class WhatsAppStatusAutomation:
    """Automates WhatsApp status updates on macOS."""
    
    def __init__(self, config_path: str = None):
        """Initialize with config file."""
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "config.json"
        )
        self.config = self.load_config()
        self.delay = self.config.get("delay_between_actions", 1.0)
    
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
                "delay_between_actions": 1.0,
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
    
    def open_whatsapp(self) -> bool:
        """Open WhatsApp application on macOS."""
        app_name = self.config.get("whatsapp_app_name", "WhatsApp")
        
        print(f"📱 Opening {app_name}...")
        
        # Use AppleScript to open and activate WhatsApp
        script = f'''
        tell application "{app_name}"
            activate
        end tell
        '''
        
        try:
            subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
            time.sleep(self.delay * 2)  # Wait for app to open
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to open {app_name}: {e}")
            return False
    
    def click_at_image(self, image_name: str, confidence: float = 0.8) -> bool:
        """Click at a location found by image matching."""
        try:
            location = pyautogui.locateOnScreen(
                os.path.join(os.path.dirname(__file__), "images", image_name),
                confidence=confidence
            )
            if location:
                center = pyautogui.center(location)
                pyautogui.click(center)
                return True
        except Exception as e:
            print(f"⚠️ Image not found: {image_name} - {e}")
        return False
    
    def navigate_to_status(self) -> bool:
        """
        Navigate to WhatsApp status section.
        
        WhatsApp Desktop for Mac navigation:
        1. Click on profile/status area (usually top-left)
        2. Or use keyboard shortcut if available
        """
        print("📍 Navigating to Status section...")
        
        time.sleep(self.delay)
        
        # Method 1: Use keyboard shortcut to open settings/status
        # WhatsApp Mac: Cmd+, opens settings, but status is different
        
        # Method 2: Click on the Status tab/icon
        # WhatsApp desktop has "Status" in the sidebar
        
        # Try clicking on "Status" text or icon in sidebar
        # The sidebar is usually on the left side of the window
        
        # Get screen size for relative positioning
        screen_width, screen_height = pyautogui.size()
        
        # WhatsApp window is typically in center or left
        # Status icon is usually in the left sidebar
        
        # First, let's try to find and click the Status tab
        # In WhatsApp Desktop, it's usually:
        # - A circle icon with a dashed border
        # - Located in the left sidebar, second or third from top
        
        # Try keyboard navigation first (more reliable)
        # Cmd+2 might switch to Status in some versions
        
        print("   Trying keyboard navigation...")
        
        # Focus on WhatsApp window
        pyautogui.hotkey('command', 'tab')
        time.sleep(0.3)
        
        # Try to click on Status in the sidebar
        # Approximate position: left side of screen, upper portion
        # This will need calibration based on your WhatsApp window position
        
        try:
            # Look for "Status" text
            status_location = pyautogui.locateOnScreen(
                os.path.join(os.path.dirname(__file__), "images", "status_tab.png"),
                confidence=0.7
            )
            if status_location:
                pyautogui.click(pyautogui.center(status_location))
                time.sleep(self.delay)
                return True
        except Exception:
            pass
        
        # Fallback: Use relative click positions
        # This assumes WhatsApp is open and visible
        print("   Using position-based navigation...")
        
        # Click approximately where Status tab would be
        # Adjust these coordinates based on your screen and WhatsApp position
        
        # Get active window position
        try:
            window_info = self.get_whatsapp_window_position()
            if window_info:
                x, y, width, height = window_info
                # Status is usually in left sidebar, about 70px from left, 150px from top
                status_x = x + 70
                status_y = y + 150
                pyautogui.click(status_x, status_y)
                time.sleep(self.delay)
                return True
        except Exception as e:
            print(f"   ⚠️ Window detection failed: {e}")
        
        return False
    
    def get_whatsapp_window_position(self) -> tuple:
        """Get WhatsApp window position using AppleScript."""
        app_name = self.config.get("whatsapp_app_name", "WhatsApp")
        
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                set frontWindow to front window
                set windowPosition to position of frontWindow
                set windowSize to size of frontWindow
                return (item 1 of windowPosition) & "," & (item 2 of windowPosition) & "," & (item 1 of windowSize) & "," & (item 2 of windowSize)
            end tell
        end tell
        '''
        
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                check=True
            )
            parts = result.stdout.strip().split(",")
            return tuple(int(p) for p in parts)
        except Exception as e:
            print(f"   Could not get window position: {e}")
            return None
    
    def set_status_text(self, caption: str) -> bool:
        """
        Set the status text/caption.
        
        After navigating to status:
        1. Click on "My Status" or the text input area
        2. Clear existing text
        3. Type new caption
        4. Save/confirm
        """
        print(f"✏️ Setting status caption: {caption}")
        
        time.sleep(self.delay)
        
        # In WhatsApp Desktop:
        # - Click on "My status" or the status update area
        # - This might open a text input or camera
        # - For text status: type the caption
        
        # Try to find and click "My status" or "Add status" button
        try:
            # Look for the status input area
            for img in ["my_status.png", "add_status.png", "status_input.png"]:
                try:
                    location = pyautogui.locateOnScreen(
                        os.path.join(os.path.dirname(__file__), "images", img),
                        confidence=0.7
                    )
                    if location:
                        pyautogui.click(pyautogui.center(location))
                        time.sleep(self.delay)
                        break
                except Exception:
                    continue
        except Exception:
            pass
        
        # Click in the text input area (center of screen, slightly below middle)
        screen_width, screen_height = pyautogui.size()
        pyautogui.click(screen_width // 2, screen_height // 2)
        time.sleep(0.5)
        
        # Clear any existing text
        pyautogui.hotkey('command', 'a')
        time.sleep(0.2)
        
        # Type the new caption
        pyautogui.typewrite(caption, interval=0.05) if caption.isascii() else self._type_unicode(caption)
        
        time.sleep(self.delay)
        
        # Press Enter or click Send/Save button
        pyautogui.press('enter')
        
        print("✅ Status caption entered!")
        return True
    
    def _type_unicode(self, text: str):
        """Type unicode text using clipboard (for emojis etc)."""
        import subprocess
        
        # Copy to clipboard
        process = subprocess.Popen(
            ['pbcopy'],
            stdin=subprocess.PIPE,
            env={'LANG': 'en_US.UTF-8'}
        )
        process.communicate(text.encode('utf-8'))
        
        # Paste from clipboard
        time.sleep(0.2)
        pyautogui.hotkey('command', 'v')
    
    def set_status(self, caption: str = None) -> bool:
        """
        Main method: Set WhatsApp status with caption.
        
        Steps:
        1. Open WhatsApp
        2. Navigate to Status
        3. Set the caption
        """
        caption = caption or self.get_caption()
        
        print("\n" + "="*50)
        print(f"🚀 WhatsApp Status Automation")
        print(f"   Caption: {caption}")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50 + "\n")
        
        # Step 1: Open WhatsApp
        if not self.open_whatsapp():
            print("❌ Failed to open WhatsApp")
            return False
        
        # Step 2: Navigate to Status
        if not self.navigate_to_status():
            print("⚠️ Navigation might have failed, continuing anyway...")
        
        # Step 3: Set status text
        if not self.set_status_text(caption):
            print("❌ Failed to set status text")
            return False
        
        # Rotate to next caption for next time
        if not self.config.get("use_random_caption", False):
            self.rotate_caption()
        
        print("\n✅ Status update complete!")
        return True
    
    def is_weekend(self) -> bool:
        """Check if today is a scheduled day (default: weekend)."""
        days = self.config.get("schedule", {}).get("days", ["saturday", "sunday"])
        today = datetime.now().strftime("%A").lower()
        return today in [d.lower() for d in days]
    
    def should_run_now(self) -> bool:
        """Check if automation should run based on schedule."""
        if not self.is_weekend():
            return False
        
        scheduled_time = self.config.get("schedule", {}).get("time", "09:00")
        current_time = datetime.now().strftime("%H:%M")
        
        # Check if within 5 minutes of scheduled time
        scheduled_hour, scheduled_min = map(int, scheduled_time.split(":"))
        current_hour, current_min = map(int, current_time.split(":"))
        
        scheduled_minutes = scheduled_hour * 60 + scheduled_min
        current_minutes = current_hour * 60 + current_min
        
        return abs(current_minutes - scheduled_minutes) <= 5


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="WhatsApp Status Automation for macOS"
    )
    parser.add_argument(
        "--run", "-r",
        action="store_true",
        help="Run the status update immediately"
    )
    parser.add_argument(
        "--caption", "-c",
        type=str,
        help="Custom caption to use (overrides config)"
    )
    parser.add_argument(
        "--schedule", "-s",
        action="store_true",
        help="Run in scheduled mode (checks if it's the right day/time)"
    )
    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Run as daemon (keeps running and checks schedule)"
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Test mode - just print what would happen"
    )
    
    args = parser.parse_args()
    
    automation = WhatsAppStatusAutomation()
    
    if args.test:
        print("🧪 TEST MODE")
        print(f"   Is weekend: {automation.is_weekend()}")
        print(f"   Should run now: {automation.should_run_now()}")
        print(f"   Caption would be: {automation.get_caption()}")
        return
    
    if args.daemon:
        print("🔄 Running in daemon mode...")
        print("   Will check schedule every minute")
        print("   Press Ctrl+C to stop\n")
        
        try:
            import schedule as sched_lib
            
            scheduled_time = automation.config.get("schedule", {}).get("time", "09:00")
            days = automation.config.get("schedule", {}).get("days", ["saturday", "sunday"])
            
            def job():
                if automation.is_weekend():
                    automation.set_status(args.caption)
            
            # Schedule for configured time on configured days
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
            print(f"   Scheduled days: {automation.config.get('schedule', {}).get('days', [])}")
        return
    
    if args.run or args.caption:
        automation.set_status(args.caption)
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()

