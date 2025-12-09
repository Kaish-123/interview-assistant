#!/usr/bin/env python3
"""
Standalone Global Hotkey Helper for macOS
Runs as a separate process with proper main run loop
Writes hotkey events to a file that the main app reads
"""
import sys
import os
import json
import time

# Create events file
EVENTS_FILE = "/tmp/ia_hotkey_events.json"

# Key codes
MAC_KEY_CODES = {
    50: 'backtick',    # ` key
    10: 'backtick',    # § key
    121: 'page_down',
    116: 'page_up',
    120: 'f2',
    53: 'escape',
}

HOTKEY_CONFIG = {
    'backtick': 'toggle_recording',
    'page_down': 'scroll_bottom',
    'page_up': 'scroll_top',
    'f2': 'save_layout',
    'escape': 'cancel_action',
}


def write_event(key_name, action):
    """Write hotkey event to file"""
    event = {
        'type': 'hotkey',
        'key': key_name,
        'action': action,
        'timestamp': time.time()
    }
    try:
        with open(EVENTS_FILE, 'w') as f:
            json.dump(event, f)
        print(f"🎹 GLOBAL: {key_name} -> {action}", flush=True)
    except Exception as e:
        print(f"Error writing event: {e}", flush=True)


def main():
    print("🎹 Global Hotkey Helper starting...", flush=True)
    
    try:
        from AppKit import NSApplication, NSEvent, NSKeyDownMask
        from PyObjCTools import AppHelper
        
        # Create minimal app
        app = NSApplication.sharedApplication()
        
        last_trigger_times = {}
        cooldown = 0.2
        
        def handler(event):
            try:
                keycode = event.keyCode()
                print(f"🔤 Keycode: {keycode}", flush=True)
                
                key_name = MAC_KEY_CODES.get(keycode)
                if key_name and key_name in HOTKEY_CONFIG:
                    current_time = time.time()
                    last_time = last_trigger_times.get(key_name, 0)
                    
                    if current_time - last_time >= cooldown:
                        last_trigger_times[key_name] = current_time
                        action = HOTKEY_CONFIG[key_name]
                        write_event(key_name, action)
            except Exception as e:
                print(f"Handler error: {e}", flush=True)
            return event
        
        # Add global monitor
        monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSKeyDownMask,
            handler
        )
        
        if monitor is None:
            print("❌ Failed to create monitor!", flush=True)
            print("⚠️ Grant Accessibility permission to Terminal/Python", flush=True)
            sys.exit(1)
        
        print("✅ Global monitor active! Press ` anywhere to test.", flush=True)
        
        # Run the app
        AppHelper.runConsoleEventLoop()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopped", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

