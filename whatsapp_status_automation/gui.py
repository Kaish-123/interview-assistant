#!/usr/bin/env python3
"""
WhatsApp Status Automation GUI
==============================
A simple GUI for configuring and running the WhatsApp status automation.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import threading
import subprocess
from datetime import datetime
from pathlib import Path

# Import the main automation class
from whatsapp_status import WhatsAppStatusAutomation


class WhatsAppStatusGUI:
    """GUI for WhatsApp Status Automation."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WhatsApp Status Automation")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Set up styles
        self.style = ttk.Style()
        self.style.theme_use('aqua' if os.uname().sysname == 'Darwin' else 'clam')
        
        # Initialize automation
        self.automation = WhatsAppStatusAutomation()
        
        self.setup_ui()
        self.load_config_to_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ===== Header =====
        header = ttk.Label(
            main_frame, 
            text="📱 WhatsApp Status Automation",
            font=('Arial', 18, 'bold')
        )
        header.pack(pady=(0, 10))
        
        # ===== Captions Section =====
        caption_frame = ttk.LabelFrame(main_frame, text="Status Captions", padding="10")
        caption_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Caption listbox
        self.caption_listbox = tk.Listbox(caption_frame, height=6, font=('Arial', 12))
        self.caption_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        caption_scrollbar = ttk.Scrollbar(caption_frame, orient=tk.VERTICAL, command=self.caption_listbox.yview)
        caption_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.caption_listbox.config(yscrollcommand=caption_scrollbar.set)
        
        # Caption buttons
        caption_btn_frame = ttk.Frame(main_frame)
        caption_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(caption_btn_frame, text="➕ Add Caption", command=self.add_caption).pack(side=tk.LEFT, padx=2)
        ttk.Button(caption_btn_frame, text="✏️ Edit Caption", command=self.edit_caption).pack(side=tk.LEFT, padx=2)
        ttk.Button(caption_btn_frame, text="🗑️ Delete Caption", command=self.delete_caption).pack(side=tk.LEFT, padx=2)
        
        # Random caption checkbox
        self.random_var = tk.BooleanVar()
        ttk.Checkbutton(
            caption_btn_frame, 
            text="Use Random Caption", 
            variable=self.random_var,
            command=self.save_config
        ).pack(side=tk.RIGHT, padx=10)
        
        # ===== Schedule Section =====
        schedule_frame = ttk.LabelFrame(main_frame, text="Schedule", padding="10")
        schedule_frame.pack(fill=tk.X, pady=5)
        
        # Days
        days_frame = ttk.Frame(schedule_frame)
        days_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(days_frame, text="Days:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.day_vars = {}
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            var = tk.BooleanVar()
            self.day_vars[day.lower()] = var
            ttk.Checkbutton(
                days_frame, 
                text=day[:3], 
                variable=var,
                command=self.save_config
            ).pack(side=tk.LEFT, padx=2)
        
        # Time
        time_frame = ttk.Frame(schedule_frame)
        time_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(time_frame, text="Time:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.hour_var = tk.StringVar(value="09")
        self.minute_var = tk.StringVar(value="00")
        
        hour_spinbox = ttk.Spinbox(
            time_frame, 
            from_=0, to=23, 
            width=3, 
            textvariable=self.hour_var,
            command=self.save_config,
            format="%02.0f"
        )
        hour_spinbox.pack(side=tk.LEFT)
        
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        
        minute_spinbox = ttk.Spinbox(
            time_frame, 
            from_=0, to=59, 
            width=3, 
            textvariable=self.minute_var,
            command=self.save_config,
            format="%02.0f"
        )
        minute_spinbox.pack(side=tk.LEFT)
        
        # ===== Action Buttons =====
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            action_frame, 
            text="▶️ Run Now",
            command=self.run_now
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame, 
            text="🧪 Test Mode",
            command=self.test_mode
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame, 
            text="📅 Setup Scheduler",
            command=self.setup_scheduler
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame, 
            text="🗑️ Remove Scheduler",
            command=self.remove_scheduler
        ).pack(side=tk.LEFT, padx=5)
        
        # ===== Status Bar =====
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            main_frame, 
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
    
    def load_config_to_ui(self):
        """Load config values into UI elements."""
        config = self.automation.config
        
        # Load captions
        self.caption_listbox.delete(0, tk.END)
        for caption in config.get("status_captions", []):
            self.caption_listbox.insert(tk.END, caption)
        
        # Load random setting
        self.random_var.set(config.get("use_random_caption", False))
        
        # Load schedule days
        schedule_days = config.get("schedule", {}).get("days", ["saturday", "sunday"])
        for day, var in self.day_vars.items():
            var.set(day in schedule_days)
        
        # Load schedule time
        schedule_time = config.get("schedule", {}).get("time", "09:00")
        hour, minute = schedule_time.split(":")
        self.hour_var.set(hour)
        self.minute_var.set(minute)
    
    def save_config(self):
        """Save UI values to config."""
        # Get captions from listbox
        captions = list(self.caption_listbox.get(0, tk.END))
        
        # Get selected days
        days = [day for day, var in self.day_vars.items() if var.get()]
        
        # Get time
        time_str = f"{int(self.hour_var.get()):02d}:{int(self.minute_var.get()):02d}"
        
        # Update config
        self.automation.config["status_captions"] = captions
        self.automation.config["use_random_caption"] = self.random_var.get()
        self.automation.config["schedule"] = {
            "days": days,
            "time": time_str
        }
        
        # Save to file
        self.automation.save_config()
        self.status_var.set(f"Config saved at {datetime.now().strftime('%H:%M:%S')}")
    
    def add_caption(self):
        """Add a new caption."""
        caption = simpledialog.askstring(
            "Add Caption",
            "Enter new status caption:",
            parent=self.root
        )
        if caption:
            self.caption_listbox.insert(tk.END, caption)
            self.save_config()
    
    def edit_caption(self):
        """Edit selected caption."""
        selection = self.caption_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a caption to edit.")
            return
        
        idx = selection[0]
        current = self.caption_listbox.get(idx)
        
        new_caption = simpledialog.askstring(
            "Edit Caption",
            "Edit status caption:",
            initialvalue=current,
            parent=self.root
        )
        
        if new_caption:
            self.caption_listbox.delete(idx)
            self.caption_listbox.insert(idx, new_caption)
            self.save_config()
    
    def delete_caption(self):
        """Delete selected caption."""
        selection = self.caption_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a caption to delete.")
            return
        
        if messagebox.askyesno("Confirm Delete", "Delete this caption?"):
            self.caption_listbox.delete(selection[0])
            self.save_config()
    
    def run_now(self):
        """Run the status update immediately."""
        self.status_var.set("Running status update...")
        self.root.update()
        
        def run():
            try:
                self.automation.set_status()
                self.root.after(0, lambda: self.status_var.set("✅ Status update complete!"))
            except Exception as e:
                self.root.after(0, lambda: self.status_var.set(f"❌ Error: {e}"))
        
        threading.Thread(target=run, daemon=True).start()
    
    def test_mode(self):
        """Show what would happen without actually doing it."""
        caption = self.automation.get_caption()
        is_weekend = self.automation.is_weekend()
        should_run = self.automation.should_run_now()
        
        message = f"""
Test Mode Results:
==================
Today: {datetime.now().strftime('%A')}
Is scheduled day: {'Yes' if is_weekend else 'No'}
Should run now: {'Yes' if should_run else 'No'}

Would use caption:
"{caption}"

Configured schedule:
Days: {', '.join(self.automation.config['schedule']['days'])}
Time: {self.automation.config['schedule']['time']}
        """
        
        messagebox.showinfo("Test Mode", message)
    
    def setup_scheduler(self):
        """Set up the system scheduler."""
        time_str = f"{int(self.hour_var.get()):02d}:{int(self.minute_var.get()):02d}"
        
        result = messagebox.askyesno(
            "Setup Scheduler",
            f"This will schedule the status update to run on:\n"
            f"Days: {', '.join(d for d, v in self.day_vars.items() if v.get())}\n"
            f"Time: {time_str}\n\n"
            "Continue?"
        )
        
        if result:
            try:
                scheduler_path = Path(__file__).parent / "scheduler.py"
                subprocess.run(
                    ["python3", str(scheduler_path), "--setup", "--time", time_str],
                    check=True
                )
                self.status_var.set("✅ Scheduler set up successfully!")
                messagebox.showinfo(
                    "Scheduler Setup",
                    "Scheduler has been set up!\n\n"
                    "Important: Make sure to grant Accessibility permissions to Python/Terminal.\n"
                    "Go to: System Preferences > Security & Privacy > Privacy > Accessibility"
                )
            except Exception as e:
                self.status_var.set(f"❌ Setup failed: {e}")
                messagebox.showerror("Error", f"Failed to set up scheduler: {e}")
    
    def remove_scheduler(self):
        """Remove the system scheduler."""
        if messagebox.askyesno("Remove Scheduler", "Remove the scheduled automation?"):
            try:
                scheduler_path = Path(__file__).parent / "scheduler.py"
                subprocess.run(
                    ["python3", str(scheduler_path), "--unload"],
                    check=True
                )
                self.status_var.set("✅ Scheduler removed")
            except Exception as e:
                self.status_var.set(f"❌ Removal failed: {e}")
    
    def run(self):
        """Start the GUI."""
        self.root.mainloop()


def main():
    gui = WhatsAppStatusGUI()
    gui.run()


if __name__ == "__main__":
    main()

