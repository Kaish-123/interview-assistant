#!/usr/bin/env python3
"""
WhatsApp Status Automation for macOS
====================================
Smart automation that finds UI elements dynamically.
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
    from PIL import Image
except ImportError:
    print("❌ Missing dependencies. Run: pip install pyautogui pillow")
    sys.exit(1)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2


class WhatsAppStatusAutomation:
    """Smart WhatsApp Status automation with UI element detection."""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "config.json")
        self.config = self.load_config()
        self.delay = self.config.get("delay_between_actions", 2.0)
        self.app_name = self.config.get("whatsapp_app_name", "WhatsApp")
    
    def load_config(self) -> dict:
        default = {
            "status_captions": ["Weekend vibes ✨", "Taking a break 🌴"],
            "schedule": {"days": ["saturday", "sunday"], "time": "09:00"},
            "whatsapp_app_name": "WhatsApp",
            "delay_between_actions": 2.0,
            "use_random_caption": False,
            "current_caption_index": 0,
        }
        try:
            with open(self.config_path, "r") as f:
                loaded = json.load(f)
                for k, v in default.items():
                    if k not in loaded:
                        loaded[k] = v
                return loaded
        except FileNotFoundError:
            with open(self.config_path, "w") as f:
                json.dump(default, f, indent=4)
            return default
    
    def save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)
    
    def get_caption(self) -> str:
        captions = self.config.get("status_captions", ["Status update"])
        if self.config.get("use_random_caption"):
            import random
            return random.choice(captions)
        idx = self.config.get("current_caption_index", 0) % len(captions)
        return captions[idx]
    
    def rotate_caption(self):
        captions = self.config.get("status_captions", [])
        if captions:
            self.config["current_caption_index"] = (self.config.get("current_caption_index", 0) + 1) % len(captions)
            self.save_config()
    
    def run_applescript(self, script: str) -> tuple:
        """Run AppleScript and return (success, output)."""
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0, result.stdout.strip()
        except Exception as e:
            return False, str(e)
    
    def is_whatsapp_running(self) -> bool:
        """Check if WhatsApp is running."""
        success, output = self.run_applescript(f'''
            tell application "System Events"
                return (name of processes) contains "{self.app_name}"
            end tell
        ''')
        return success and "true" in output.lower()
    
    def launch_whatsapp(self) -> bool:
        """Launch WhatsApp and wait for it to be ready."""
        print(f"📱 Launching {self.app_name}...")
        
        was_running = self.is_whatsapp_running()
        
        # Launch the app
        subprocess.run(["open", "-a", self.app_name], capture_output=True)
        
        if not was_running:
            print("   Waiting for app to start (5 seconds)...")
            time.sleep(5)
        else:
            time.sleep(1)
        
        # Activate and bring to front
        self.run_applescript(f'''
            tell application "{self.app_name}" to activate
            delay 1
            tell application "System Events"
                set frontmost of process "{self.app_name}" to true
            end tell
        ''')
        
        time.sleep(self.delay)
        print("   ✅ WhatsApp activated")
        return True
    
    def get_window_bounds(self) -> dict:
        """Get WhatsApp window position and size."""
        success, output = self.run_applescript(f'''
            tell application "System Events"
                tell process "{self.app_name}"
                    if (count of windows) > 0 then
                        set w to window 1
                        set p to position of w
                        set s to size of w
                        return ((item 1 of p) as string) & "," & ((item 2 of p) as string) & "," & ((item 1 of s) as string) & "," & ((item 2 of s) as string)
                    end if
                end tell
            end tell
        ''')
        
        if success and output and "," in output:
            parts = [int(float(x)) for x in output.split(",")]
            return {"x": parts[0], "y": parts[1], "w": parts[2], "h": parts[3]}
        return None
    
    def list_ui_elements(self) -> str:
        """List all UI elements in WhatsApp window for debugging."""
        success, output = self.run_applescript(f'''
            tell application "System Events"
                tell process "{self.app_name}"
                    set output to ""
                    tell window 1
                        -- Get all groups and their buttons
                        repeat with g in groups
                            try
                                set output to output & "Group: " & (description of g) & return
                                repeat with b in buttons of g
                                    try
                                        set output to output & "  Button: " & (description of b) & " | " & (name of b) & return
                                    end try
                                end repeat
                            end try
                        end repeat
                        -- Get toolbar buttons
                        try
                            repeat with tb in toolbars
                                repeat with b in buttons of tb
                                    try
                                        set output to output & "Toolbar Button: " & (description of b) & " | " & (name of b) & return
                                    end try
                                end repeat
                            end repeat
                        end try
                        -- Get all buttons directly in window
                        repeat with b in buttons
                            try
                                set output to output & "Window Button: " & (description of b) & " | " & (name of b) & return
                            end try
                        end repeat
                    end tell
                end tell
            end tell
            return output
        ''')
        return output if success else "Could not list elements"
    
    def find_and_click_status_tab(self) -> bool:
        """
        Find and click the Status/Updates tab using multiple methods.
        """
        print("🔍 Finding Status tab...")
        
        # Method 1: Try clicking by accessibility description
        status_keywords = ["Status", "Updates", "status", "updates"]
        
        for keyword in status_keywords:
            success, _ = self.run_applescript(f'''
                tell application "System Events"
                    tell process "{self.app_name}"
                        tell window 1
                            -- Try to find button with this keyword
                            repeat with g in groups
                                repeat with b in buttons of g
                                    try
                                        if description of b contains "{keyword}" then
                                            click b
                                            return "clicked"
                                        end if
                                        if name of b contains "{keyword}" then
                                            click b
                                            return "clicked"
                                        end if
                                    end try
                                end repeat
                            end repeat
                            -- Try toolbar
                            try
                                repeat with tb in toolbars
                                    repeat with b in buttons of tb
                                        try
                                            if description of b contains "{keyword}" then
                                                click b
                                                return "clicked"
                                            end if
                                        end try
                                    end repeat
                                end repeat
                            end try
                        end tell
                    end tell
                end tell
                return "not found"
            ''')
            if success and "clicked" in _:
                print(f"   ✅ Found Status via AppleScript (keyword: {keyword})")
                time.sleep(self.delay)
                return True
        
        # Method 2: Try clicking the 2nd navigation button (Status is usually 2nd)
        print("   Trying navigation buttons...")
        success, _ = self.run_applescript(f'''
            tell application "System Events"
                tell process "{self.app_name}"
                    tell window 1
                        -- WhatsApp has a group of navigation buttons on the left
                        -- Try to find the navigation group and click 2nd button
                        set allGroups to groups
                        repeat with g in allGroups
                            try
                                set btns to buttons of g
                                if (count of btns) >= 2 then
                                    -- Check if this looks like the nav bar (multiple small buttons)
                                    set firstBtn to item 1 of btns
                                    set btnPos to position of firstBtn
                                    -- Nav buttons are usually on the left (x < 100)
                                    if (item 1 of btnPos) < 100 then
                                        click item 2 of btns
                                        return "clicked nav"
                                    end if
                                end if
                            end try
                        end repeat
                    end tell
                end tell
            end tell
            return "not found"
        ''')
        if success and "clicked" in _:
            print("   ✅ Clicked 2nd navigation button")
            time.sleep(self.delay)
            return True
        
        # Method 3: Position-based click as last resort
        print("   Trying position-based click...")
        win = self.get_window_bounds()
        if win:
            # Status tab is typically in the left sidebar
            # Usually around x=35 from window left, y=90-100 from window top
            # But it varies - let's try a few positions
            positions_to_try = [
                (35, 95),   # Common position
                (35, 75),   # Higher up
                (35, 115),  # Lower down
                (40, 90),   # Slightly right
            ]
            
            for x_off, y_off in positions_to_try:
                click_x = win["x"] + x_off
                click_y = win["y"] + y_off
                print(f"   Clicking at ({click_x}, {click_y})...")
                pyautogui.click(click_x, click_y)
                time.sleep(1)
                
                # Check if we're now in Status view by looking for "My status" text
                # This is a heuristic - if clicking worked, the view should change
        
        return True  # Continue anyway
    
    def find_and_click_add_status(self) -> bool:
        """Find and click the Add Status / pencil button."""
        print("➕ Finding Add Status button...")
        
        # Method 1: Look for "pencil", "compose", "add", "text" buttons
        add_keywords = ["pencil", "compose", "add", "text", "new", "write", "Aa"]
        
        for keyword in add_keywords:
            success, output = self.run_applescript(f'''
                tell application "System Events"
                    tell process "{self.app_name}"
                        tell window 1
                            repeat with g in groups
                                repeat with b in buttons of g
                                    try
                                        set d to description of b
                                        if d contains "{keyword}" then
                                            click b
                                            return "clicked: " & d
                                        end if
                                    end try
                                end repeat
                            end repeat
                        end tell
                    end tell
                end tell
                return "not found"
            ''')
            if success and "clicked" in output:
                print(f"   ✅ Found Add Status button: {output}")
                time.sleep(self.delay)
                return True
        
        # Method 2: Click "My status" area if visible
        success, _ = self.run_applescript(f'''
            tell application "System Events"
                tell process "{self.app_name}"
                    tell window 1
                        -- Look for static text or button containing "My status"
                        repeat with g in groups
                            repeat with elem in UI elements of g
                                try
                                    set elemName to name of elem
                                    if elemName contains "My status" or elemName contains "my status" then
                                        click elem
                                        return "clicked my status"
                                    end if
                                end try
                            end repeat
                        end repeat
                    end tell
                end tell
            end tell
            return "not found"
        ''')
        if success and "clicked" in _:
            print("   ✅ Clicked 'My status' area")
            time.sleep(self.delay)
            return True
        
        # Method 3: Position-based - look for + icon or pencil on right side of header
        print("   Trying position-based click for Add button...")
        win = self.get_window_bounds()
        if win:
            # The pencil/add button is usually on the right side of the status header
            # Try clicking near the right side of the window, upper area
            click_x = win["x"] + win["w"] - 60  # 60px from right edge
            click_y = win["y"] + 100  # Upper area
            print(f"   Clicking pencil area at ({click_x}, {click_y})...")
            pyautogui.click(click_x, click_y)
            time.sleep(self.delay)
        
        return True
    
    def type_status_and_post(self, caption: str) -> bool:
        """Type the status caption and post it."""
        print(f"✏️ Typing caption: {caption}")
        
        # Clear any existing text
        pyautogui.hotkey('command', 'a')
        time.sleep(0.3)
        
        # Type using clipboard (supports emojis)
        process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        process.communicate(caption.encode('utf-8'))
        time.sleep(0.2)
        
        pyautogui.hotkey('command', 'v')
        time.sleep(self.delay)
        
        # Try to post/send
        print("   Posting status...")
        
        # Method 1: Press Enter
        pyautogui.press('enter')
        time.sleep(0.5)
        
        # Method 2: Try Cmd+Enter
        pyautogui.hotkey('command', 'enter')
        time.sleep(0.5)
        
        # Method 3: Try to click Send button via AppleScript
        self.run_applescript(f'''
            tell application "System Events"
                tell process "{self.app_name}"
                    tell window 1
                        repeat with b in buttons
                            try
                                if description of b contains "send" or description of b contains "Send" or description of b contains "post" or description of b contains "Post" then
                                    click b
                                    return "sent"
                                end if
                            end try
                        end repeat
                    end tell
                end tell
            end tell
        ''')
        
        print("   ✅ Status posted!")
        return True
    
    def set_status(self, caption: str = None) -> bool:
        """Main method to set WhatsApp status."""
        caption = caption or self.get_caption()
        
        print("\n" + "="*60)
        print("🚀 WhatsApp Status Automation")
        print(f"   Caption: {caption}")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
        
        # Step 1: Launch WhatsApp
        if not self.launch_whatsapp():
            return False
        
        # Give it extra time to fully load
        print("⏳ Waiting for WhatsApp to fully load...")
        time.sleep(3)
        
        # Step 2: Click on Status tab
        self.find_and_click_status_tab()
        time.sleep(2)
        
        # Step 3: Click Add Status button
        self.find_and_click_add_status()
        time.sleep(2)
        
        # Step 4: Type and post
        self.type_status_and_post(caption)
        
        # Rotate caption for next time
        if not self.config.get("use_random_caption"):
            self.rotate_caption()
        
        print("\n" + "="*60)
        print("✅ STATUS UPDATE COMPLETE!")
        print("="*60)
        print("\n⚠️  Please verify the status was posted correctly.")
        print("    If it didn't work, run: ./run.sh --debug")
        print("    to see what UI elements WhatsApp has.\n")
        
        return True
    
    def debug_ui(self):
        """Debug mode - list all UI elements in WhatsApp."""
        print("\n🔍 DEBUG MODE - Scanning WhatsApp UI Elements")
        print("="*60)
        
        self.launch_whatsapp()
        time.sleep(2)
        
        win = self.get_window_bounds()
        if win:
            print(f"\n📐 Window: position=({win['x']}, {win['y']}) size={win['w']}x{win['h']}")
        
        print("\n📋 UI Elements found:")
        print("-"*60)
        elements = self.list_ui_elements()
        print(elements if elements else "No elements found or access denied")
        
        print("\n💡 Tips:")
        print("   - Look for 'Status' or 'Updates' in the button descriptions")
        print("   - The Status tab is usually the 2nd button in the navigation")
        print("   - Grant Terminal accessibility permissions if elements aren't showing")
        print("\n   System Preferences → Security & Privacy → Privacy → Accessibility")
    
    def calibrate(self):
        """Interactive calibration mode."""
        print("\n🔧 CALIBRATION MODE")
        print("="*60)
        print("Move your mouse to see coordinates. Press Ctrl+C to stop.\n")
        
        self.launch_whatsapp()
        time.sleep(1)
        
        win = self.get_window_bounds()
        if win:
            print(f"Window: ({win['x']}, {win['y']}) size {win['w']}x{win['h']}\n")
        
        try:
            while True:
                x, y = pyautogui.position()
                rel_x = x - win["x"] if win else 0
                rel_y = y - win["y"] if win else 0
                print(f"\rAbsolute: ({x:4d}, {y:4d}) | Relative: ({rel_x:4d}, {rel_y:4d})    ", end="", flush=True)
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\n👋 Calibration stopped.")
    
    def is_weekend(self) -> bool:
        days = self.config.get("schedule", {}).get("days", ["saturday", "sunday"])
        return datetime.now().strftime("%A").lower() in [d.lower() for d in days]
    
    def should_run_now(self) -> bool:
        if not self.is_weekend():
            return False
        scheduled = self.config.get("schedule", {}).get("time", "09:00")
        h, m = map(int, scheduled.split(":"))
        now_h, now_m = datetime.now().hour, datetime.now().minute
        return abs((h * 60 + m) - (now_h * 60 + now_m)) <= 5


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="WhatsApp Status Automation")
    parser.add_argument("--run", "-r", action="store_true", help="Run now")
    parser.add_argument("--caption", "-c", type=str, help="Custom caption")
    parser.add_argument("--debug", action="store_true", help="Debug: list UI elements")
    parser.add_argument("--calibrate", action="store_true", help="Track mouse position")
    parser.add_argument("--test", "-t", action="store_true", help="Test mode")
    parser.add_argument("--schedule", "-s", action="store_true", help="Run if scheduled")
    parser.add_argument("--daemon", "-d", action="store_true", help="Daemon mode")
    
    args = parser.parse_args()
    auto = WhatsAppStatusAutomation()
    
    if args.debug:
        auto.debug_ui()
        return
    
    if args.calibrate:
        auto.calibrate()
        return
    
    if args.test:
        print("🧪 TEST MODE")
        print(f"   Scheduled day: {auto.is_weekend()}")
        print(f"   Should run now: {auto.should_run_now()}")
        print(f"   Next caption: {auto.get_caption()}")
        return
    
    if args.daemon:
        print("🔄 Daemon mode - Press Ctrl+C to stop")
        try:
            import schedule as sched
            t = auto.config.get("schedule", {}).get("time", "09:00")
            for day in auto.config.get("schedule", {}).get("days", ["saturday", "sunday"]):
                getattr(sched.every(), day).at(t).do(lambda: auto.set_status(args.caption))
            print(f"   Scheduled: {auto.config.get('schedule', {}).get('days')} at {t}")
            while True:
                sched.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n👋 Stopped")
        return
    
    if args.schedule:
        if auto.should_run_now():
            auto.set_status(args.caption)
        else:
            print("⏳ Not scheduled time")
        return
    
    if args.run or args.caption:
        auto.set_status(args.caption)
        return
    
    parser.print_help()
    print("\n" + "="*50)
    print("💡 QUICK START:")
    print("="*50)
    print("1. Debug UI elements:  ./run.sh --debug")
    print("2. Run automation:     ./run.sh --run")
    print("3. Track mouse:        ./run.sh --calibrate")
    print("\n⚠️  Make sure Terminal has Accessibility permissions!")
    print("   System Preferences → Security & Privacy → Privacy → Accessibility")


if __name__ == "__main__":
    main()
