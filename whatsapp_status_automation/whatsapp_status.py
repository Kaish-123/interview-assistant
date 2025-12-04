#!/usr/bin/env python3
"""
WhatsApp Status Automation for macOS
====================================
Automatically sets your WhatsApp Status (Stories) on weekends.

Uses AppleScript UI automation for reliable element detection.
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
pyautogui.FAILSAFE = True
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
        default_config = {
            "status_captions": ["Weekend vibes ✨"],
            "schedule": {"days": ["saturday", "sunday"], "time": "09:00"},
            "whatsapp_app_name": "WhatsApp",
            "delay_between_actions": 1.5,
            "use_random_caption": False,
            "current_caption_index": 0,
            # Calibrated positions (relative to window)
            "positions": {
                "status_tab": {"x_offset": 35, "y_offset": 95},  # Status icon in sidebar
                "add_status_button": {"x_offset": 120, "y_offset": 95},  # + button or My Status
                "text_status_icon": {"x_offset": -80, "y_offset": 95},  # Pencil icon (from right)
            }
        }
        
        try:
            with open(self.config_path, "r") as f:
                loaded = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in loaded:
                        loaded[key] = value
                return loaded
        except FileNotFoundError:
            print(f"⚠️ Config not found, creating with defaults")
            with open(self.config_path, "w") as f:
                json.dump(default_config, f, indent=4)
            return default_config
    
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
    
    def get_window_info(self) -> dict:
        """Get WhatsApp window position and size using AppleScript."""
        app_name = self.config.get("whatsapp_app_name", "WhatsApp")
        
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                if (count of windows) > 0 then
                    set win to window 1
                    set winPos to position of win
                    set winSize to size of win
                    return (item 1 of winPos as string) & "," & (item 2 of winPos as string) & "," & (item 1 of winSize as string) & "," & (item 2 of winSize as string)
                else
                    return "error:no_window"
                end if
            end tell
        end tell
        '''
        
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip() and "error" not in result.stdout:
                parts = result.stdout.strip().split(",")
                x, y, w, h = [int(float(p)) for p in parts]
                return {"x": x, "y": y, "width": w, "height": h}
        except Exception as e:
            print(f"   ⚠️ Window detection error: {e}")
        
        return None
    
    def open_whatsapp(self) -> bool:
        """Open WhatsApp and bring it to front."""
        app_name = self.config.get("whatsapp_app_name", "WhatsApp")
        print(f"📱 Opening {app_name}...")
        
        # Open the app
        subprocess.run(["open", "-a", app_name], capture_output=True)
        time.sleep(2)
        
        # Bring to front and activate
        script = f'''
        tell application "{app_name}" to activate
        delay 0.5
        tell application "System Events"
            set frontmost of process "{app_name}" to true
        end tell
        '''
        subprocess.run(["osascript", "-e", script], capture_output=True)
        time.sleep(1)
        
        # Verify window exists
        win = self.get_window_info()
        if win:
            print(f"   ✅ Window found at ({win['x']}, {win['y']}) size {win['width']}x{win['height']}")
            return True
        else:
            print("   ⚠️ Could not detect window, continuing anyway...")
            return True
    
    def click_status_tab_applescript(self) -> bool:
        """Try to click Status tab using AppleScript UI automation."""
        app_name = self.config.get("whatsapp_app_name", "WhatsApp")
        
        # Try to find and click "Status" or "Updates" button/tab
        # WhatsApp uses different names in different versions
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                -- Try to find Status/Updates in the UI
                set found to false
                
                -- Look for buttons or UI elements with Status-related names
                try
                    -- Try clicking the second toolbar button (Status is usually 2nd)
                    set toolbarButtons to buttons of toolbar 1 of window 1
                    if (count of toolbarButtons) >= 2 then
                        click item 2 of toolbarButtons
                        set found to true
                    end if
                end try
                
                if not found then
                    -- Try looking for "Status" or "Updates" text
                    try
                        click button "Status" of window 1
                        set found to true
                    end try
                end if
                
                if not found then
                    try
                        click button "Updates" of window 1
                        set found to true
                    end try
                end if
                
                return found
            end tell
        end tell
        '''
        
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and "true" in result.stdout.lower():
                print("   ✅ Found Status via AppleScript")
                return True
        except Exception as e:
            print(f"   AppleScript method failed: {e}")
        
        return False
    
    def click_at_position(self, name: str, win: dict, use_right_offset: bool = False) -> bool:
        """Click at a configured position relative to window."""
        positions = self.config.get("positions", {})
        pos = positions.get(name, {})
        
        x_offset = pos.get("x_offset", 35)
        y_offset = pos.get("y_offset", 100)
        
        if use_right_offset:
            # Calculate from right side of window
            click_x = win["x"] + win["width"] + x_offset
        else:
            click_x = win["x"] + x_offset
        
        click_y = win["y"] + y_offset
        
        print(f"   Clicking '{name}' at ({click_x}, {click_y})...")
        pyautogui.click(click_x, click_y)
        time.sleep(self.delay)
        return True
    
    def click_status_tab(self) -> bool:
        """Click on Status tab in sidebar."""
        print("📍 Clicking Status tab...")
        
        # First try AppleScript (most reliable if it works)
        if self.click_status_tab_applescript():
            time.sleep(self.delay)
            return True
        
        # Fallback to position-based clicking
        win = self.get_window_info()
        if not win:
            print("   ❌ Cannot get window position")
            return False
        
        # Use configured position
        return self.click_at_position("status_tab", win)
    
    def click_add_status(self) -> bool:
        """Click the Add Status button."""
        print("➕ Clicking Add Status button...")
        
        win = self.get_window_info()
        if not win:
            return False
        
        # Try the + button or My Status area
        self.click_at_position("add_status_button", win)
        time.sleep(0.5)
        
        # Also try the pencil/text icon on the right side
        self.click_at_position("text_status_icon", win, use_right_offset=True)
        
        return True
    
    def type_and_post(self, caption: str) -> bool:
        """Type the status caption and post it."""
        print(f"✏️ Typing: {caption}")
        
        time.sleep(0.5)
        
        # Type using clipboard (supports emojis)
        process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        process.communicate(caption.encode('utf-8'))
        time.sleep(0.2)
        pyautogui.hotkey('command', 'v')
        time.sleep(self.delay)
        
        # Post the status
        print("   Posting...")
        pyautogui.press('enter')
        time.sleep(0.5)
        
        return True
    
    def set_status(self, caption: str = None) -> bool:
        """Main method: Set WhatsApp Status."""
        caption = caption or self.get_caption()
        
        print("\n" + "="*50)
        print("🚀 WhatsApp Status Automation")
        print(f"   Caption: {caption}")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50 + "\n")
        
        if not self.open_whatsapp():
            return False
        
        if not self.click_status_tab():
            print("⚠️ Status tab click may have failed...")
        time.sleep(1)
        
        if not self.click_add_status():
            print("⚠️ Add status click may have failed...")
        time.sleep(1)
        
        if not self.type_and_post(caption):
            return False
        
        if not self.config.get("use_random_caption", False):
            self.rotate_caption()
        
        print("\n✅ Status update complete!")
        return True
    
    def setup_wizard(self):
        """Interactive setup wizard to configure click positions."""
        print("\n" + "="*60)
        print("🔧 WHATSAPP STATUS AUTOMATION - SETUP WIZARD")
        print("="*60)
        print("\nThis will help you configure the correct click positions.")
        print("WhatsApp will open, and you'll click on elements to save their positions.\n")
        
        input("Press Enter to start...")
        
        # Open WhatsApp
        self.open_whatsapp()
        time.sleep(2)
        
        win = self.get_window_info()
        if not win:
            print("❌ Could not detect WhatsApp window!")
            return
        
        print(f"\n📐 Window detected at: ({win['x']}, {win['y']}) size: {win['width']}x{win['height']}")
        
        # Initialize positions
        if "positions" not in self.config:
            self.config["positions"] = {}
        
        positions_to_configure = [
            ("status_tab", "STATUS TAB (circle icon with dashes in sidebar)"),
            ("add_status_button", "ADD STATUS button (+ icon or 'My status' area)"),
        ]
        
        for pos_name, description in positions_to_configure:
            print(f"\n{'='*60}")
            print(f"📍 Step: Click on the {description}")
            print("="*60)
            print("\nMove your mouse to the correct position.")
            print("The position will be captured in 5 seconds...")
            print("(Move mouse to screen corner to abort)")
            
            for i in range(5, 0, -1):
                print(f"   {i}...", end=" ", flush=True)
                time.sleep(1)
            print()
            
            # Capture position
            mouse_x, mouse_y = pyautogui.position()
            
            # Convert to offset from window
            x_offset = mouse_x - win["x"]
            y_offset = mouse_y - win["y"]
            
            self.config["positions"][pos_name] = {
                "x_offset": x_offset,
                "y_offset": y_offset
            }
            
            print(f"   ✅ Saved: offset ({x_offset}, {y_offset}) from window top-left")
            print(f"   Absolute position was: ({mouse_x}, {mouse_y})")
        
        # Also configure the text/pencil icon position (usually on right side)
        print(f"\n{'='*60}")
        print("📍 Step: Click on the TEXT/PENCIL icon (for text status)")
        print("="*60)
        print("\nThis is usually on the right side of the window.")
        print("If you don't see it, just position over where it should be.")
        print("Move your mouse there. Capturing in 5 seconds...")
        
        for i in range(5, 0, -1):
            print(f"   {i}...", end=" ", flush=True)
            time.sleep(1)
        print()
        
        mouse_x, mouse_y = pyautogui.position()
        # Store as offset from right edge (negative)
        x_offset = mouse_x - (win["x"] + win["width"])
        y_offset = mouse_y - win["y"]
        
        self.config["positions"]["text_status_icon"] = {
            "x_offset": x_offset,
            "y_offset": y_offset
        }
        print(f"   ✅ Saved: offset ({x_offset}, {y_offset}) from window top-right")
        
        # Save config
        self.save_config()
        
        print("\n" + "="*60)
        print("✅ SETUP COMPLETE!")
        print("="*60)
        print(f"\nPositions saved to: {self.config_path}")
        print("\nYou can now run: ./run.sh --run")
        print("\nSaved positions:")
        for name, pos in self.config["positions"].items():
            print(f"   {name}: x_offset={pos['x_offset']}, y_offset={pos['y_offset']}")
    
    def calibrate(self):
        """Real-time mouse position tracking."""
        print("\n🔧 CALIBRATION MODE - Real-time Mouse Tracking")
        print("="*50)
        print("Move your mouse around WhatsApp to see coordinates.")
        print("Press Ctrl+C to stop.\n")
        
        self.open_whatsapp()
        time.sleep(1)
        
        win = self.get_window_info()
        if win:
            print(f"Window: ({win['x']}, {win['y']}) size {win['width']}x{win['height']}\n")
        
        try:
            while True:
                x, y = pyautogui.position()
                if win:
                    rel_x = x - win["x"]
                    rel_y = y - win["y"]
                    print(f"\rAbsolute: ({x:4d}, {y:4d})  |  Relative to window: ({rel_x:4d}, {rel_y:4d})    ", end="", flush=True)
                else:
                    print(f"\rPosition: ({x:4d}, {y:4d})    ", end="", flush=True)
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\n👋 Calibration stopped.")
    
    def is_weekend(self) -> bool:
        days = self.config.get("schedule", {}).get("days", ["saturday", "sunday"])
        today = datetime.now().strftime("%A").lower()
        return today in [d.lower() for d in days]
    
    def should_run_now(self) -> bool:
        if not self.is_weekend():
            return False
        scheduled_time = self.config.get("schedule", {}).get("time", "09:00")
        scheduled_hour, scheduled_min = map(int, scheduled_time.split(":"))
        current_hour, current_min = datetime.now().hour, datetime.now().minute
        scheduled_minutes = scheduled_hour * 60 + scheduled_min
        current_minutes = current_hour * 60 + current_min
        return abs(current_minutes - scheduled_minutes) <= 5


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="WhatsApp Status Automation for macOS")
    parser.add_argument("--run", "-r", action="store_true", help="Run status update now")
    parser.add_argument("--caption", "-c", type=str, help="Custom caption")
    parser.add_argument("--setup", action="store_true", help="Run setup wizard to configure positions")
    parser.add_argument("--calibrate", action="store_true", help="Real-time mouse position tracking")
    parser.add_argument("--test", "-t", action="store_true", help="Test mode")
    parser.add_argument("--schedule", "-s", action="store_true", help="Run only if scheduled")
    parser.add_argument("--daemon", "-d", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    automation = WhatsAppStatusAutomation()
    
    if args.setup:
        automation.setup_wizard()
        return
    
    if args.calibrate:
        automation.calibrate()
        return
    
    if args.test:
        print("🧪 TEST MODE")
        print(f"   Is scheduled day: {automation.is_weekend()}")
        print(f"   Should run now: {automation.should_run_now()}")
        print(f"   Caption would be: {automation.get_caption()}")
        print(f"\n   Configured positions:")
        for name, pos in automation.config.get("positions", {}).items():
            print(f"      {name}: {pos}")
        return
    
    if args.daemon:
        print("🔄 Running in daemon mode... Press Ctrl+C to stop\n")
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
            print("\n👋 Stopped")
        return
    
    if args.schedule:
        if automation.should_run_now():
            automation.set_status(args.caption)
        else:
            print("⏳ Not scheduled time")
        return
    
    if args.run or args.caption:
        automation.set_status(args.caption)
        return
    
    # Default: show help
    parser.print_help()
    print("\n" + "="*50)
    print("💡 QUICK START:")
    print("="*50)
    print("1. First run setup wizard to configure positions:")
    print("   ./run.sh --setup")
    print("\n2. Then run the automation:")
    print("   ./run.sh --run")
    print("\n3. Or track mouse position in real-time:")
    print("   ./run.sh --calibrate")


if __name__ == "__main__":
    main()
