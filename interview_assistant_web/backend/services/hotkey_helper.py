#!/usr/bin/env python3
"""
Standalone Global Hotkey Helper for macOS
Uses pynput for keyboard monitoring (requires Accessibility permissions)
Writes hotkey events to a file that the main app reads
"""
import sys
import os
import json
import time

# Create events file
EVENTS_FILE = "/tmp/ia_hotkey_events.json"

# Key mappings for pynput
HOTKEY_MAPPING = {
    '`': ('backtick', 'toggle_recording'),
    'Key.page_down': ('page_down', 'scroll_bottom'),
    'Key.page_up': ('page_up', 'scroll_top'),
    'Key.f2': ('f2', 'save_layout'),
    'Key.esc': ('escape', 'cancel_action'),
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
        print(f"🎹 GLOBAL HOTKEY: {key_name} -> {action}", flush=True)
    except Exception as e:
        print(f"Error writing event: {e}", flush=True)


def try_pynput():
    """Try using pynput for global hotkeys"""
    print("📌 Trying pynput method...", flush=True)
    
    try:
        from pynput import keyboard
        
        last_trigger_times = {}
        cooldown = 0.3  # Prevent double triggers
        
        def on_press(key):
            try:
                # Get key string representation
                key_str = None
                
                # Check for character keys
                try:
                    key_str = key.char
                except AttributeError:
                    # Special key
                    key_str = str(key)
                
                # Check if it's a mapped hotkey
                mapping = HOTKEY_MAPPING.get(key_str)
                if mapping:
                    key_name, action = mapping
                    current_time = time.time()
                    last_time = last_trigger_times.get(key_name, 0)
                    
                    if current_time - last_time >= cooldown:
                        last_trigger_times[key_name] = current_time
                        write_event(key_name, action)
                else:
                    # Debug output for unmapped keys
                    if key_str and key_str not in ['Key.shift', 'Key.cmd', 'Key.ctrl', 'Key.alt', 'Key.caps_lock']:
                        print(f"🔤 Key pressed: {key_str}", flush=True)
                        
            except Exception as e:
                print(f"Key handler error: {e}", flush=True)
        
        # Create and start listener
        print("✅ Starting pynput global keyboard listener...", flush=True)
        print("⚠️  If no keys are detected, grant Accessibility permission to Terminal/Python", flush=True)
        print("   Go to: System Preferences > Security & Privacy > Privacy > Accessibility", flush=True)
        print("", flush=True)
        print("🎹 Press ` (backtick) anywhere to test!", flush=True)
        
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
            
    except ImportError:
        print("❌ pynput not installed. Install with: pip install pynput", flush=True)
        return False
    except Exception as e:
        print(f"❌ pynput error: {e}", flush=True)
        return False
    
    return True


def try_nsevents():
    """Try using NSEvents for global hotkeys (macOS native)"""
    print("📌 Trying NSEvent method...", flush=True)
    
    try:
        from AppKit import NSApplication, NSEvent, NSKeyDownMask
        from PyObjCTools import AppHelper
        
        # Create minimal app
        app = NSApplication.sharedApplication()
        
        last_trigger_times = {}
        cooldown = 0.3
        
        # Key codes for macOS
        MAC_KEY_CODES = {
            50: ('backtick', 'toggle_recording'),    # ` key
            10: ('backtick', 'toggle_recording'),    # § key (alternative)
            121: ('page_down', 'scroll_bottom'),
            116: ('page_up', 'scroll_top'),
            120: ('f2', 'save_layout'),
            53: ('escape', 'cancel_action'),
        }
        
        def handler(event):
            try:
                keycode = event.keyCode()
                
                mapping = MAC_KEY_CODES.get(keycode)
                if mapping:
                    key_name, action = mapping
                    current_time = time.time()
                    last_time = last_trigger_times.get(key_name, 0)
                    
                    if current_time - last_time >= cooldown:
                        last_trigger_times[key_name] = current_time
                        write_event(key_name, action)
                else:
                    # Debug: print keycode for unknown keys
                    chars = event.characters()
                    if chars and chars.strip():
                        print(f"🔤 Keycode: {keycode}, Char: {chars}", flush=True)
                        
            except Exception as e:
                print(f"Handler error: {e}", flush=True)
            return event
        
        # Add global monitor
        monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSKeyDownMask,
            handler
        )
        
        if monitor is None:
            print("❌ Failed to create NSEvent monitor!", flush=True)
            print("⚠️  Grant Accessibility permission to Terminal/Python", flush=True)
            return False
        
        print("✅ NSEvent global monitor active!", flush=True)
        print("🎹 Press ` (backtick) anywhere to test!", flush=True)
        
        # Run the app
        AppHelper.runConsoleEventLoop()
        
    except ImportError:
        print("❌ PyObjC not installed", flush=True)
        return False
    except Exception as e:
        print(f"❌ NSEvent error: {e}", flush=True)
        return False
    
    return True


def main():
    print("=" * 50, flush=True)
    print("🎹 Global Hotkey Helper for Interview Assistant", flush=True)
    print("=" * 50, flush=True)
    print("", flush=True)
    
    # Try pynput first (simpler, more reliable)
    if try_pynput():
        return
    
    print("", flush=True)
    print("Falling back to NSEvent...", flush=True)
    print("", flush=True)
    
    # Fall back to NSEvent
    if try_nsevents():
        return
    
    print("", flush=True)
    print("❌ All methods failed!", flush=True)
    print("Please ensure:", flush=True)
    print("1. pynput is installed: pip install pynput", flush=True)
    print("2. Accessibility permission is granted to Terminal/Python", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Stopped", flush=True)
