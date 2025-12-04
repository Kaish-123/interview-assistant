#!/usr/bin/env python3
"""
WhatsApp Marketing GUI
Beautiful interface to manage contacts, campaigns, and scheduling
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import os
import sys
import threading
from datetime import datetime
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Import our modules
from contact_fetcher import (
    refresh_contacts, get_all_contacts_with_status, get_contacts_for_messaging,
    exclude_contact, include_contact, get_contact_stats, load_config as load_contact_config
)
from whatsapp_marketing import (
    load_config, save_config, get_marketing_images, run_marketing_campaign,
    IMAGES_DIR, LOG_DIR
)
from marketing_scheduler import setup_schedule, unload_schedule, check_status


class MarketingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📱 WhatsApp Marketing Manager")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Configure style
        self.setup_styles()
        
        # Load configuration
        self.config = load_config()
        
        # Create main notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_contacts_tab()
        self.create_message_tab()
        self.create_images_tab()
        self.create_schedule_tab()
        self.create_logs_tab()
        
        # Refresh data
        self.refresh_all_data()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief='sunken', anchor='w')
        status_bar.pack(fill='x', side='bottom', padx=10, pady=5)
    
    def setup_styles(self):
        """Configure custom styles."""
        style = ttk.Style()
        
        # Try to use a modern theme
        available_themes = style.theme_names()
        if 'aqua' in available_themes:
            style.theme_use('aqua')
        elif 'clam' in available_themes:
            style.theme_use('clam')
        
        # Custom colors
        style.configure('Title.TLabel', font=('Helvetica', 24, 'bold'))
        style.configure('Subtitle.TLabel', font=('Helvetica', 14))
        style.configure('Stat.TLabel', font=('Helvetica', 32, 'bold'))
        style.configure('StatLabel.TLabel', font=('Helvetica', 11))
        
        # Button styles
        style.configure('Action.TButton', font=('Helvetica', 12), padding=10)
        style.configure('Danger.TButton', font=('Helvetica', 11))
        style.configure('Success.TButton', font=('Helvetica', 11))
        
        # Treeview style
        style.configure('Treeview', rowheight=30, font=('Helvetica', 11))
        style.configure('Treeview.Heading', font=('Helvetica', 11, 'bold'))
    
    def create_dashboard_tab(self):
        """Create the main dashboard tab."""
        dashboard = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(dashboard, text="📊 Dashboard")
        
        # Title
        title = ttk.Label(dashboard, text="WhatsApp Marketing Dashboard", style='Title.TLabel')
        title.pack(pady=(0, 20))
        
        # Stats frame
        stats_frame = ttk.LabelFrame(dashboard, text="📈 Statistics", padding=20)
        stats_frame.pack(fill='x', pady=10)
        
        # Create stat boxes
        self.stat_vars = {}
        stat_items = [
            ('total_contacts', 'Total Contacts', '0'),
            ('active_contacts', 'Active', '0'),
            ('excluded_contacts', 'Excluded', '0'),
            ('images_count', 'Images', '0'),
            ('messaged_today', 'Sent Today', '0')
        ]
        
        for i, (key, label, default) in enumerate(stat_items):
            frame = ttk.Frame(stats_frame)
            frame.pack(side='left', expand=True, padx=20)
            
            self.stat_vars[key] = tk.StringVar(value=default)
            stat_label = ttk.Label(frame, textvariable=self.stat_vars[key], style='Stat.TLabel')
            stat_label.pack()
            
            name_label = ttk.Label(frame, text=label, style='StatLabel.TLabel')
            name_label.pack()
        
        # Quick actions frame
        actions_frame = ttk.LabelFrame(dashboard, text="⚡ Quick Actions", padding=20)
        actions_frame.pack(fill='x', pady=20)
        
        btn_frame = ttk.Frame(actions_frame)
        btn_frame.pack()
        
        # Refresh contacts button
        refresh_btn = ttk.Button(
            btn_frame, text="🔄 Refresh Contacts",
            command=self.refresh_contacts_action, style='Action.TButton'
        )
        refresh_btn.pack(side='left', padx=10)
        
        # Run campaign button
        run_btn = ttk.Button(
            btn_frame, text="🚀 Run Campaign",
            command=self.run_campaign_action, style='Action.TButton'
        )
        run_btn.pack(side='left', padx=10)
        
        # Dry run button
        test_btn = ttk.Button(
            btn_frame, text="🧪 Test Run (Dry)",
            command=self.dry_run_action, style='Action.TButton'
        )
        test_btn.pack(side='left', padx=10)
        
        # Open images folder
        folder_btn = ttk.Button(
            btn_frame, text="📁 Open Images Folder",
            command=self.open_images_folder, style='Action.TButton'
        )
        folder_btn.pack(side='left', padx=10)
        
        # Contact breakdown
        breakdown_frame = ttk.LabelFrame(dashboard, text="📋 Contacts by Type", padding=20)
        breakdown_frame.pack(fill='both', expand=True, pady=10)
        
        self.breakdown_text = tk.Text(breakdown_frame, height=8, font=('Helvetica', 12))
        self.breakdown_text.pack(fill='both', expand=True)
        self.breakdown_text.config(state='disabled')
    
    def create_contacts_tab(self):
        """Create the contacts management tab."""
        contacts = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(contacts, text="👥 Contacts")
        
        # Top toolbar
        toolbar = ttk.Frame(contacts)
        toolbar.pack(fill='x', pady=(0, 10))
        
        # Refresh button
        refresh_btn = ttk.Button(toolbar, text="🔄 Refresh from macOS", command=self.refresh_contacts_action)
        refresh_btn.pack(side='left', padx=5)
        
        # Filter dropdown
        ttk.Label(toolbar, text="Filter:").pack(side='left', padx=(20, 5))
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(toolbar, textvariable=self.filter_var, values=["All", "client", "proxy", "interview"], width=15)
        filter_combo.pack(side='left')
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.update_contacts_list())
        
        # Search
        ttk.Label(toolbar, text="Search:").pack(side='left', padx=(20, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        search_entry.pack(side='left')
        search_entry.bind('<KeyRelease>', lambda e: self.update_contacts_list())
        
        # Bulk actions
        ttk.Label(toolbar, text="Selected:").pack(side='left', padx=(30, 5))
        exclude_btn = ttk.Button(toolbar, text="❌ Exclude", command=self.exclude_selected)
        exclude_btn.pack(side='left', padx=2)
        include_btn = ttk.Button(toolbar, text="✅ Include", command=self.include_selected)
        include_btn.pack(side='left', padx=2)
        
        # Contacts treeview
        columns = ('name', 'phone', 'type', 'status', 'last_sent', 'count')
        self.contacts_tree = ttk.Treeview(contacts, columns=columns, show='headings', selectmode='extended')
        
        # Configure columns
        self.contacts_tree.heading('name', text='Name')
        self.contacts_tree.heading('phone', text='Phone')
        self.contacts_tree.heading('type', text='Type')
        self.contacts_tree.heading('status', text='Status')
        self.contacts_tree.heading('last_sent', text='Last Sent')
        self.contacts_tree.heading('count', text='Count')
        
        self.contacts_tree.column('name', width=250)
        self.contacts_tree.column('phone', width=150)
        self.contacts_tree.column('type', width=100)
        self.contacts_tree.column('status', width=100)
        self.contacts_tree.column('last_sent', width=120)
        self.contacts_tree.column('count', width=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(contacts, orient='vertical', command=self.contacts_tree.yview)
        self.contacts_tree.configure(yscrollcommand=scrollbar.set)
        
        self.contacts_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Double-click to toggle
        self.contacts_tree.bind('<Double-1>', self.toggle_contact_status)
        
        # Right-click context menu
        self.contacts_menu = tk.Menu(self.root, tearoff=0)
        self.contacts_menu.add_command(label="✅ Include", command=self.include_selected)
        self.contacts_menu.add_command(label="❌ Exclude", command=self.exclude_selected)
        self.contacts_tree.bind('<Button-2>', self.show_context_menu)
        self.contacts_tree.bind('<Button-3>', self.show_context_menu)
    
    def create_message_tab(self):
        """Create the message template tab."""
        message = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(message, text="💬 Message")
        
        # Title
        ttk.Label(message, text="Message Template", style='Subtitle.TLabel').pack(anchor='w', pady=(0, 10))
        
        # Message text area
        self.message_text = scrolledtext.ScrolledText(message, height=10, font=('Helvetica', 13), wrap='word')
        self.message_text.pack(fill='x', pady=10)
        self.message_text.insert('1.0', self.config.get('message_template', ''))
        
        # Save button
        save_frame = ttk.Frame(message)
        save_frame.pack(fill='x', pady=10)
        
        save_btn = ttk.Button(save_frame, text="💾 Save Message", command=self.save_message)
        save_btn.pack(side='left')
        
        # Preview
        ttk.Label(message, text="Preview:", style='Subtitle.TLabel').pack(anchor='w', pady=(20, 10))
        
        preview_frame = ttk.LabelFrame(message, text="📱 How it will look", padding=15)
        preview_frame.pack(fill='both', expand=True)
        
        self.preview_label = ttk.Label(preview_frame, wraplength=500, font=('Helvetica', 12))
        self.preview_label.pack(anchor='w')
        
        # Update preview on text change
        self.message_text.bind('<KeyRelease>', self.update_preview)
        self.update_preview()
        
        # Settings
        settings_frame = ttk.LabelFrame(message, text="⚙️ Campaign Settings", padding=15)
        settings_frame.pack(fill='x', pady=20)
        
        # Delay settings
        delay_frame = ttk.Frame(settings_frame)
        delay_frame.pack(fill='x', pady=5)
        
        ttk.Label(delay_frame, text="Delay between messages (seconds):").pack(side='left')
        
        ttk.Label(delay_frame, text="Min:").pack(side='left', padx=(20, 5))
        self.delay_min_var = tk.StringVar(value=str(self.config.get('delay_min_seconds', 45)))
        delay_min_entry = ttk.Entry(delay_frame, textvariable=self.delay_min_var, width=8)
        delay_min_entry.pack(side='left')
        
        ttk.Label(delay_frame, text="Max:").pack(side='left', padx=(20, 5))
        self.delay_max_var = tk.StringVar(value=str(self.config.get('delay_max_seconds', 120)))
        delay_max_entry = ttk.Entry(delay_frame, textvariable=self.delay_max_var, width=8)
        delay_max_entry.pack(side='left')
        
        # Batch settings
        batch_frame = ttk.Frame(settings_frame)
        batch_frame.pack(fill='x', pady=5)
        
        ttk.Label(batch_frame, text="Batch size:").pack(side='left')
        self.batch_var = tk.StringVar(value=str(self.config.get('batch_size', 50)))
        batch_entry = ttk.Entry(batch_frame, textvariable=self.batch_var, width=8)
        batch_entry.pack(side='left', padx=10)
        
        ttk.Label(batch_frame, text="Pause between batches (minutes):").pack(side='left', padx=(20, 0))
        self.pause_var = tk.StringVar(value=str(self.config.get('pause_between_batches_minutes', 30)))
        pause_entry = ttk.Entry(batch_frame, textvariable=self.pause_var, width=8)
        pause_entry.pack(side='left', padx=10)
        
        # Save settings button
        save_settings_btn = ttk.Button(settings_frame, text="💾 Save Settings", command=self.save_settings)
        save_settings_btn.pack(pady=10)
    
    def create_images_tab(self):
        """Create the images management tab."""
        images = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(images, text="🖼️ Images")
        
        # Title and folder path
        header_frame = ttk.Frame(images)
        header_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(header_frame, text="Marketing Images", style='Subtitle.TLabel').pack(side='left')
        
        open_folder_btn = ttk.Button(header_frame, text="📁 Open Folder", command=self.open_images_folder)
        open_folder_btn.pack(side='right')
        
        add_images_btn = ttk.Button(header_frame, text="➕ Add Images", command=self.add_images)
        add_images_btn.pack(side='right', padx=10)
        
        # Folder path
        path_label = ttk.Label(images, text=f"📂 {IMAGES_DIR}", font=('Helvetica', 10))
        path_label.pack(anchor='w', pady=(0, 10))
        
        # Images list
        list_frame = ttk.Frame(images)
        list_frame.pack(fill='both', expand=True)
        
        # Treeview for images
        columns = ('filename', 'size')
        self.images_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        self.images_tree.heading('filename', text='Filename')
        self.images_tree.heading('size', text='Size')
        
        self.images_tree.column('filename', width=400)
        self.images_tree.column('size', width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.images_tree.yview)
        self.images_tree.configure(yscrollcommand=scrollbar.set)
        
        self.images_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Info
        info_frame = ttk.Frame(images)
        info_frame.pack(fill='x', pady=10)
        
        self.images_count_label = ttk.Label(info_frame, text="0 images")
        self.images_count_label.pack(side='left')
        
        ttk.Label(info_frame, text="(WhatsApp allows max 30 images per message)", font=('Helvetica', 10)).pack(side='left', padx=20)
    
    def create_schedule_tab(self):
        """Create the scheduling tab."""
        schedule = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(schedule, text="📅 Schedule")
        
        # Title
        ttk.Label(schedule, text="Campaign Schedule", style='Subtitle.TLabel').pack(anchor='w', pady=(0, 20))
        
        # Current schedule status
        status_frame = ttk.LabelFrame(schedule, text="Current Status", padding=20)
        status_frame.pack(fill='x', pady=10)
        
        self.schedule_status_text = tk.Text(status_frame, height=6, font=('Courier', 11))
        self.schedule_status_text.pack(fill='x')
        self.schedule_status_text.config(state='disabled')
        
        # Schedule settings
        settings_frame = ttk.LabelFrame(schedule, text="⚙️ Configure Schedule", padding=20)
        settings_frame.pack(fill='x', pady=20)
        
        # Day selection
        day_frame = ttk.Frame(settings_frame)
        day_frame.pack(fill='x', pady=10)
        
        ttk.Label(day_frame, text="Day:").pack(side='left')
        self.schedule_day_var = tk.StringVar(value="saturday")
        day_combo = ttk.Combobox(day_frame, textvariable=self.schedule_day_var, 
                                  values=["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
                                  width=15)
        day_combo.pack(side='left', padx=10)
        
        ttk.Label(day_frame, text="Time (24hr):").pack(side='left', padx=(30, 0))
        self.schedule_time_var = tk.StringVar(value="02:00")
        time_entry = ttk.Entry(day_frame, textvariable=self.schedule_time_var, width=10)
        time_entry.pack(side='left', padx=10)
        
        ttk.Label(day_frame, text="IST", font=('Helvetica', 10)).pack(side='left')
        
        # Buttons
        btn_frame = ttk.Frame(settings_frame)
        btn_frame.pack(pady=20)
        
        setup_btn = ttk.Button(btn_frame, text="✅ Set Up Schedule", command=self.setup_schedule_action, style='Action.TButton')
        setup_btn.pack(side='left', padx=10)
        
        remove_btn = ttk.Button(btn_frame, text="❌ Remove Schedule", command=self.remove_schedule_action)
        remove_btn.pack(side='left', padx=10)
        
        refresh_btn = ttk.Button(btn_frame, text="🔄 Refresh Status", command=self.refresh_schedule_status)
        refresh_btn.pack(side='left', padx=10)
        
        # Info
        info_frame = ttk.LabelFrame(schedule, text="ℹ️ Important Notes", padding=15)
        info_frame.pack(fill='x', pady=10)
        
        info_text = """• Your Mac must be ON at the scheduled time (can be sleeping)
• The automation will attempt to unlock your screen automatically
• Make sure WhatsApp Desktop is installed and logged in
• Test with a dry run before setting up the schedule
• Logs are saved to ~/Library/Logs/whatsapp_marketing.log"""
        
        ttk.Label(info_frame, text=info_text, font=('Helvetica', 11), justify='left').pack(anchor='w')
    
    def create_logs_tab(self):
        """Create the logs tab."""
        logs = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(logs, text="📋 Logs")
        
        # Toolbar
        toolbar = ttk.Frame(logs)
        toolbar.pack(fill='x', pady=(0, 10))
        
        refresh_btn = ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_logs)
        refresh_btn.pack(side='left')
        
        clear_btn = ttk.Button(toolbar, text="🗑️ Clear Logs", command=self.clear_logs)
        clear_btn.pack(side='left', padx=10)
        
        open_btn = ttk.Button(toolbar, text="📂 Open Log Folder", command=self.open_logs_folder)
        open_btn.pack(side='left', padx=10)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(logs, font=('Courier', 10))
        self.log_text.pack(fill='both', expand=True)
        self.log_text.config(state='disabled')
    
    # ============= Actions =============
    
    def refresh_all_data(self):
        """Refresh all data in the GUI."""
        self.update_stats()
        self.update_contacts_list()
        self.update_images_list()
        self.refresh_schedule_status()
        self.refresh_logs()
    
    def update_stats(self):
        """Update the dashboard statistics."""
        try:
            stats = get_contact_stats()
            images = get_marketing_images()
            
            self.stat_vars['total_contacts'].set(str(stats.get('total', 0)))
            self.stat_vars['active_contacts'].set(str(stats.get('active', 0)))
            self.stat_vars['excluded_contacts'].set(str(stats.get('excluded', 0)))
            self.stat_vars['images_count'].set(str(len(images)))
            self.stat_vars['messaged_today'].set(str(stats.get('messaged_today', 0)))
            
            # Update breakdown
            self.breakdown_text.config(state='normal')
            self.breakdown_text.delete('1.0', 'end')
            
            breakdown = stats.get('by_suffix', {})
            if breakdown:
                for suffix, count in breakdown.items():
                    self.breakdown_text.insert('end', f"   {suffix.upper()}: {count} contacts\n")
            else:
                self.breakdown_text.insert('end', "   No contacts found. Click 'Refresh Contacts' to sync from macOS.\n")
            
            self.breakdown_text.config(state='disabled')
            
        except Exception as e:
            print(f"Error updating stats: {e}")
    
    def update_contacts_list(self):
        """Update the contacts treeview."""
        # Clear existing
        for item in self.contacts_tree.get_children():
            self.contacts_tree.delete(item)
        
        try:
            contacts = get_all_contacts_with_status()
            
            # Apply filters
            filter_type = self.filter_var.get()
            search_term = self.search_var.get().lower()
            
            for contact in contacts:
                # Filter by type
                if filter_type != "All" and contact['suffix_type'] != filter_type:
                    continue
                
                # Filter by search
                if search_term and search_term not in contact['name'].lower() and search_term not in contact['phone']:
                    continue
                
                # Format values
                status = "❌ Excluded" if contact['is_excluded'] else "✅ Active"
                last_sent = contact['last_messaged'][:10] if contact['last_messaged'] else "Never"
                
                self.contacts_tree.insert('', 'end', iid=contact['id'], values=(
                    contact['name'],
                    contact['phone'],
                    contact['suffix_type'],
                    status,
                    last_sent,
                    contact['message_count']
                ))
                
        except Exception as e:
            print(f"Error updating contacts: {e}")
    
    def update_images_list(self):
        """Update the images treeview."""
        # Clear existing
        for item in self.images_tree.get_children():
            self.images_tree.delete(item)
        
        images = get_marketing_images()
        
        for img_path in images:
            filename = os.path.basename(img_path)
            size = os.path.getsize(img_path)
            size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024*1024):.1f} MB"
            
            self.images_tree.insert('', 'end', values=(filename, size_str))
        
        self.images_count_label.config(text=f"{len(images)} images")
    
    def refresh_contacts_action(self):
        """Refresh contacts from macOS Contacts app."""
        self.status_var.set("Refreshing contacts...")
        self.root.update()
        
        def do_refresh():
            try:
                result = refresh_contacts()
                self.root.after(0, lambda: self.on_refresh_complete(result))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to refresh contacts: {e}"))
        
        threading.Thread(target=do_refresh, daemon=True).start()
    
    def on_refresh_complete(self, result):
        """Callback when contact refresh is complete."""
        if 'error' in result:
            messagebox.showerror("Error", result['error'])
        else:
            messagebox.showinfo(
                "Contacts Refreshed",
                f"Fetched: {result.get('fetched', 0)}\n"
                f"New: {result.get('new', 0)}\n"
                f"Total: {result.get('total', 0)}\n"
                f"Active: {result.get('active', 0)}"
            )
        
        self.update_stats()
        self.update_contacts_list()
        self.status_var.set("Ready")
    
    def exclude_selected(self):
        """Exclude selected contacts."""
        selected = self.contacts_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select contacts to exclude")
            return
        
        for contact_id in selected:
            exclude_contact(contact_id)
        
        self.update_contacts_list()
        self.update_stats()
        self.status_var.set(f"Excluded {len(selected)} contacts")
    
    def include_selected(self):
        """Include selected contacts."""
        selected = self.contacts_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select contacts to include")
            return
        
        for contact_id in selected:
            include_contact(contact_id)
        
        self.update_contacts_list()
        self.update_stats()
        self.status_var.set(f"Included {len(selected)} contacts")
    
    def toggle_contact_status(self, event):
        """Toggle contact exclusion status on double-click."""
        item = self.contacts_tree.selection()
        if item:
            contact_id = item[0]
            values = self.contacts_tree.item(contact_id, 'values')
            current_status = values[3]
            
            if "Excluded" in current_status:
                include_contact(contact_id)
            else:
                exclude_contact(contact_id)
            
            self.update_contacts_list()
            self.update_stats()
    
    def show_context_menu(self, event):
        """Show right-click context menu."""
        try:
            self.contacts_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.contacts_menu.grab_release()
    
    def save_message(self):
        """Save the message template."""
        message = self.message_text.get('1.0', 'end-1c')
        self.config['message_template'] = message
        save_config(self.config)
        self.status_var.set("Message saved!")
        messagebox.showinfo("Saved", "Message template saved successfully!")
    
    def save_settings(self):
        """Save campaign settings."""
        try:
            self.config['delay_min_seconds'] = int(self.delay_min_var.get())
            self.config['delay_max_seconds'] = int(self.delay_max_var.get())
            self.config['batch_size'] = int(self.batch_var.get())
            self.config['pause_between_batches_minutes'] = int(self.pause_var.get())
            save_config(self.config)
            self.status_var.set("Settings saved!")
            messagebox.showinfo("Saved", "Settings saved successfully!")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for all settings")
    
    def update_preview(self, event=None):
        """Update the message preview."""
        message = self.message_text.get('1.0', 'end-1c')
        self.preview_label.config(text=message if message else "(Empty message)")
    
    def open_images_folder(self):
        """Open the marketing images folder in Finder."""
        subprocess.run(["open", IMAGES_DIR])
    
    def add_images(self):
        """Add images via file dialog."""
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.gif *.webp")]
        )
        
        if files:
            import shutil
            for file_path in files:
                filename = os.path.basename(file_path)
                dest = os.path.join(IMAGES_DIR, filename)
                shutil.copy2(file_path, dest)
            
            self.update_images_list()
            self.update_stats()
            messagebox.showinfo("Added", f"Added {len(files)} images")
    
    def open_logs_folder(self):
        """Open the logs folder."""
        subprocess.run(["open", LOG_DIR])
    
    def refresh_logs(self):
        """Refresh the logs display."""
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', 'end')
        
        # Find today's log file
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(LOG_DIR, f"marketing_{today}.log")
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                self.log_text.insert('end', f.read())
        else:
            # Try to find any log file
            log_files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith('.log')], reverse=True)
            if log_files:
                with open(os.path.join(LOG_DIR, log_files[0]), 'r') as f:
                    self.log_text.insert('end', f"=== {log_files[0]} ===\n\n")
                    self.log_text.insert('end', f.read())
            else:
                self.log_text.insert('end', "No logs found yet.\n\nRun a campaign to generate logs.")
        
        self.log_text.config(state='disabled')
        self.log_text.see('end')  # Scroll to bottom
    
    def clear_logs(self):
        """Clear all log files."""
        if messagebox.askyesno("Clear Logs", "Are you sure you want to clear all logs?"):
            for f in os.listdir(LOG_DIR):
                if f.endswith('.log'):
                    os.remove(os.path.join(LOG_DIR, f))
            self.refresh_logs()
            self.status_var.set("Logs cleared")
    
    def refresh_schedule_status(self):
        """Refresh the schedule status display."""
        self.schedule_status_text.config(state='normal')
        self.schedule_status_text.delete('1.0', 'end')
        
        # Capture check_status output
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            check_status()
        
        output = f.getvalue()
        self.schedule_status_text.insert('end', output)
        self.schedule_status_text.config(state='disabled')
    
    def setup_schedule_action(self):
        """Set up the schedule."""
        day = self.schedule_day_var.get()
        time_str = self.schedule_time_var.get()
        
        try:
            # Validate time format
            hour, minute = map(int, time_str.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError()
        except:
            messagebox.showerror("Error", "Invalid time format. Use HH:MM (e.g., 02:00)")
            return
        
        if messagebox.askyesno("Confirm", f"Set up schedule for {day.capitalize()} at {time_str} IST?"):
            setup_schedule(time_str, day)
            self.refresh_schedule_status()
            messagebox.showinfo("Success", "Schedule set up successfully!")
    
    def remove_schedule_action(self):
        """Remove the schedule."""
        if messagebox.askyesno("Confirm", "Remove the scheduled campaign?"):
            unload_schedule()
            self.refresh_schedule_status()
            messagebox.showinfo("Removed", "Schedule removed")
    
    def run_campaign_action(self):
        """Run the marketing campaign."""
        stats = get_contact_stats()
        images = get_marketing_images()
        
        message = f"""Are you sure you want to run the campaign?

📊 Contacts to message: {stats.get('active', 0)}
🖼️ Images to send: {len(images)}

This will send messages to ALL active contacts.
The process may take several hours depending on the number of contacts."""
        
        if not messagebox.askyesno("Confirm Campaign", message):
            return
        
        self.status_var.set("Running campaign...")
        
        def do_campaign():
            try:
                result = run_marketing_campaign(dry_run=False)
                self.root.after(0, lambda: self.on_campaign_complete(result))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Campaign failed: {e}"))
                self.root.after(0, lambda: self.status_var.set("Campaign failed"))
        
        threading.Thread(target=do_campaign, daemon=True).start()
    
    def dry_run_action(self):
        """Run a dry test of the campaign."""
        self.status_var.set("Running dry test...")
        
        def do_dry_run():
            try:
                result = run_marketing_campaign(dry_run=True, limit=5)
                self.root.after(0, lambda: self.on_campaign_complete(result, is_dry=True))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Dry run failed: {e}"))
                self.root.after(0, lambda: self.status_var.set("Dry run failed"))
        
        threading.Thread(target=do_dry_run, daemon=True).start()
    
    def on_campaign_complete(self, result, is_dry=False):
        """Callback when campaign completes."""
        prefix = "[DRY RUN] " if is_dry else ""
        messagebox.showinfo(
            f"{prefix}Campaign Complete",
            f"✅ Successful: {result.get('success', 0)}\n"
            f"❌ Failed: {result.get('failed', 0)}\n"
            f"📋 Total: {result.get('total', 0)}"
        )
        self.update_stats()
        self.refresh_logs()
        self.status_var.set("Ready")


def main():
    root = tk.Tk()
    
    # Set app icon (if available)
    try:
        root.iconphoto(True, tk.PhotoImage(file=os.path.join(SCRIPT_DIR, 'icon.png')))
    except:
        pass
    
    app = MarketingGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

