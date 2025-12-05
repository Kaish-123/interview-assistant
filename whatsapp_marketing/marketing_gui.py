#!/usr/bin/env python3
"""
WhatsApp Marketing GUI - Optimized & Responsive
Fast, fluid interface for managing contacts, campaigns, and scheduling
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import os
import sys
import threading
from datetime import datetime
import subprocess
from concurrent.futures import ThreadPoolExecutor
import queue

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Thread pool for background operations
executor = ThreadPoolExecutor(max_workers=4)

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
        
        # Cache for data
        self._contacts_cache = []
        self._images_cache = []
        self._stats_cache = {}
        
        # Queue for thread-safe UI updates
        self.update_queue = queue.Queue()
        
        # Configure style
        self.setup_styles()
        
        # Load configuration (fast, from file)
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
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief='sunken', anchor='w')
        status_bar.pack(fill='x', side='bottom', padx=10, pady=5)
        
        # Process update queue
        self.process_queue()
        
        # Load data in background after UI is ready
        self.root.after(100, self.initial_load)
    
    def process_queue(self):
        """Process pending UI updates from background threads."""
        try:
            while True:
                func, args = self.update_queue.get_nowait()
                func(*args)
        except queue.Empty:
            pass
        # Schedule next check
        self.root.after(50, self.process_queue)
    
    def queue_update(self, func, *args):
        """Queue a UI update to run on main thread."""
        self.update_queue.put((func, args))
    
    def initial_load(self):
        """Load initial data in background."""
        self.status_var.set("Loading...")
        executor.submit(self._load_all_data)
    
    def _load_all_data(self):
        """Background: Load all data."""
        try:
            # Load stats
            self._stats_cache = get_contact_stats()
            self.queue_update(self._update_stats_ui)
            
            # Load contacts
            self._contacts_cache = get_all_contacts_with_status()
            self.queue_update(self._update_contacts_ui)
            
            # Load images
            self._images_cache = get_marketing_images()
            self.queue_update(self._update_images_ui)
            
            self.queue_update(self.status_var.set, "Ready")
        except Exception as e:
            self.queue_update(self.status_var.set, f"Error: {e}")
    
    def setup_styles(self):
        """Configure custom styles."""
        style = ttk.Style()
        
        # Use native theme
        available_themes = style.theme_names()
        if 'aqua' in available_themes:
            style.theme_use('aqua')
        elif 'clam' in available_themes:
            style.theme_use('clam')
        
        # Custom fonts
        style.configure('Title.TLabel', font=('Helvetica', 24, 'bold'))
        style.configure('Subtitle.TLabel', font=('Helvetica', 14))
        style.configure('Stat.TLabel', font=('Helvetica', 32, 'bold'))
        style.configure('StatLabel.TLabel', font=('Helvetica', 11))
        style.configure('Action.TButton', font=('Helvetica', 12), padding=10)
        style.configure('Treeview', rowheight=28, font=('Helvetica', 11))
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
            ('total_contacts', 'Total Contacts', '—'),
            ('active_contacts', 'Active', '—'),
            ('excluded_contacts', 'Excluded', '—'),
            ('images_count', 'Images', '—'),
            ('messaged_today', 'Sent Today', '—')
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
        
        ttk.Button(btn_frame, text="🔄 Refresh Contacts", command=self.refresh_contacts_action, style='Action.TButton').pack(side='left', padx=10)
        ttk.Button(btn_frame, text="🚀 Run Campaign", command=self.run_campaign_action, style='Action.TButton').pack(side='left', padx=10)
        ttk.Button(btn_frame, text="🧪 Test Run", command=self.dry_run_action, style='Action.TButton').pack(side='left', padx=10)
        ttk.Button(btn_frame, text="📁 Images Folder", command=self.open_images_folder, style='Action.TButton').pack(side='left', padx=10)
        
        # Contact breakdown
        breakdown_frame = ttk.LabelFrame(dashboard, text="📋 Contacts by Type", padding=20)
        breakdown_frame.pack(fill='both', expand=True, pady=10)
        
        self.breakdown_text = tk.Text(breakdown_frame, height=8, font=('Helvetica', 12), state='disabled')
        self.breakdown_text.pack(fill='both', expand=True)
    
    def create_contacts_tab(self):
        """Create the contacts management tab."""
        contacts = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(contacts, text="👥 Contacts")
        
        # Top toolbar
        toolbar = ttk.Frame(contacts)
        toolbar.pack(fill='x', pady=(0, 10))
        
        ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_contacts_action).pack(side='left', padx=5)
        
        ttk.Label(toolbar, text="Filter:").pack(side='left', padx=(20, 5))
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(toolbar, textvariable=self.filter_var, values=["All", "client", "proxy", "interview"], width=12, state='readonly')
        filter_combo.pack(side='left')
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_filters())
        
        ttk.Label(toolbar, text="Search:").pack(side='left', padx=(20, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=25)
        search_entry.pack(side='left')
        search_entry.bind('<KeyRelease>', lambda e: self.root.after(150, self._apply_filters))
        
        ttk.Label(toolbar, text="Selected:").pack(side='left', padx=(30, 5))
        ttk.Button(toolbar, text="❌ Exclude", command=self.exclude_selected).pack(side='left', padx=2)
        ttk.Button(toolbar, text="✅ Include", command=self.include_selected).pack(side='left', padx=2)
        
        # Contacts treeview with frame
        tree_frame = ttk.Frame(contacts)
        tree_frame.pack(fill='both', expand=True)
        
        columns = ('name', 'phone', 'type', 'status', 'last_sent', 'count')
        self.contacts_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode='extended')
        
        self.contacts_tree.heading('name', text='Name')
        self.contacts_tree.heading('phone', text='Phone')
        self.contacts_tree.heading('type', text='Type')
        self.contacts_tree.heading('status', text='Status')
        self.contacts_tree.heading('last_sent', text='Last Sent')
        self.contacts_tree.heading('count', text='Count')
        
        self.contacts_tree.column('name', width=250, minwidth=150)
        self.contacts_tree.column('phone', width=140, minwidth=100)
        self.contacts_tree.column('type', width=90, minwidth=70)
        self.contacts_tree.column('status', width=100, minwidth=80)
        self.contacts_tree.column('last_sent', width=100, minwidth=80)
        self.contacts_tree.column('count', width=60, minwidth=50)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.contacts_tree.yview)
        self.contacts_tree.configure(yscrollcommand=scrollbar.set)
        
        self.contacts_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Double-click to toggle
        self.contacts_tree.bind('<Double-1>', self.toggle_contact_status)
        
        # Right-click menu
        self.contacts_menu = tk.Menu(self.root, tearoff=0)
        self.contacts_menu.add_command(label="✅ Include", command=self.include_selected)
        self.contacts_menu.add_command(label="❌ Exclude", command=self.exclude_selected)
        self.contacts_tree.bind('<Button-2>', self.show_context_menu)
        self.contacts_tree.bind('<Button-3>', self.show_context_menu)
        
        # Count label
        self.contacts_count_var = tk.StringVar(value="0 contacts")
        ttk.Label(contacts, textvariable=self.contacts_count_var).pack(anchor='w', pady=5)
    
    def create_message_tab(self):
        """Create the message template tab."""
        message = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(message, text="💬 Message")
        
        ttk.Label(message, text="Message Template", style='Subtitle.TLabel').pack(anchor='w', pady=(0, 10))
        
        self.message_text = scrolledtext.ScrolledText(message, height=8, font=('Helvetica', 13), wrap='word')
        self.message_text.pack(fill='x', pady=10)
        self.message_text.insert('1.0', self.config.get('message_template', ''))
        
        ttk.Button(message, text="💾 Save Message", command=self.save_message).pack(anchor='w', pady=10)
        
        # Settings
        settings_frame = ttk.LabelFrame(message, text="⚙️ Campaign Settings", padding=15)
        settings_frame.pack(fill='x', pady=20)
        
        # Delay settings row
        row1 = ttk.Frame(settings_frame)
        row1.pack(fill='x', pady=8)
        
        ttk.Label(row1, text="Delay between messages:").pack(side='left')
        ttk.Label(row1, text="Min").pack(side='left', padx=(20, 5))
        self.delay_min_var = tk.StringVar(value=str(self.config.get('delay_min_seconds', 45)))
        ttk.Entry(row1, textvariable=self.delay_min_var, width=6).pack(side='left')
        ttk.Label(row1, text="sec").pack(side='left', padx=(2, 15))
        
        ttk.Label(row1, text="Max").pack(side='left', padx=(0, 5))
        self.delay_max_var = tk.StringVar(value=str(self.config.get('delay_max_seconds', 120)))
        ttk.Entry(row1, textvariable=self.delay_max_var, width=6).pack(side='left')
        ttk.Label(row1, text="sec").pack(side='left', padx=2)
        
        # Batch settings row
        row2 = ttk.Frame(settings_frame)
        row2.pack(fill='x', pady=8)
        
        ttk.Label(row2, text="Batch size:").pack(side='left')
        self.batch_var = tk.StringVar(value=str(self.config.get('batch_size', 50)))
        ttk.Entry(row2, textvariable=self.batch_var, width=6).pack(side='left', padx=(10, 20))
        
        ttk.Label(row2, text="Pause between batches:").pack(side='left')
        self.pause_var = tk.StringVar(value=str(self.config.get('pause_between_batches_minutes', 30)))
        ttk.Entry(row2, textvariable=self.pause_var, width=6).pack(side='left', padx=(10, 5))
        ttk.Label(row2, text="min").pack(side='left')
        
        ttk.Button(settings_frame, text="💾 Save Settings", command=self.save_settings).pack(pady=15)
    
    def create_images_tab(self):
        """Create the images management tab."""
        images = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(images, text="🖼️ Images")
        
        header = ttk.Frame(images)
        header.pack(fill='x', pady=(0, 10))
        
        ttk.Label(header, text="Marketing Images", style='Subtitle.TLabel').pack(side='left')
        ttk.Button(header, text="📁 Open Folder", command=self.open_images_folder).pack(side='right')
        ttk.Button(header, text="➕ Add Images", command=self.add_images).pack(side='right', padx=10)
        ttk.Button(header, text="🔄 Refresh", command=self.refresh_images).pack(side='right')
        
        ttk.Label(images, text=f"📂 {IMAGES_DIR}", font=('Helvetica', 10)).pack(anchor='w', pady=(0, 10))
        
        # Images list
        list_frame = ttk.Frame(images)
        list_frame.pack(fill='both', expand=True)
        
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
        
        info_frame = ttk.Frame(images)
        info_frame.pack(fill='x', pady=10)
        
        self.images_count_label = ttk.Label(info_frame, text="0 images")
        self.images_count_label.pack(side='left')
        ttk.Label(info_frame, text="(WhatsApp allows max 30 images per message)", font=('Helvetica', 10)).pack(side='left', padx=20)
    
    def create_schedule_tab(self):
        """Create the scheduling tab."""
        schedule = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(schedule, text="📅 Schedule")
        
        ttk.Label(schedule, text="Campaign Schedule", style='Subtitle.TLabel').pack(anchor='w', pady=(0, 20))
        
        # Status
        status_frame = ttk.LabelFrame(schedule, text="Current Status", padding=15)
        status_frame.pack(fill='x', pady=10)
        
        self.schedule_status_text = tk.Text(status_frame, height=5, font=('Courier', 11), state='disabled')
        self.schedule_status_text.pack(fill='x')
        
        # Configure
        settings_frame = ttk.LabelFrame(schedule, text="⚙️ Configure Schedule", padding=20)
        settings_frame.pack(fill='x', pady=20)
        
        config_row = ttk.Frame(settings_frame)
        config_row.pack(fill='x', pady=10)
        
        ttk.Label(config_row, text="Day:").pack(side='left')
        self.schedule_day_var = tk.StringVar(value="saturday")
        ttk.Combobox(config_row, textvariable=self.schedule_day_var, 
                     values=["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
                     width=12, state='readonly').pack(side='left', padx=10)
        
        ttk.Label(config_row, text="Time (24hr):").pack(side='left', padx=(30, 5))
        self.schedule_time_var = tk.StringVar(value="02:00")
        ttk.Entry(config_row, textvariable=self.schedule_time_var, width=8).pack(side='left')
        ttk.Label(config_row, text="IST").pack(side='left', padx=5)
        
        btn_frame = ttk.Frame(settings_frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="✅ Set Up Schedule", command=self.setup_schedule_action, style='Action.TButton').pack(side='left', padx=10)
        ttk.Button(btn_frame, text="❌ Remove Schedule", command=self.remove_schedule_action).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_schedule_status).pack(side='left', padx=10)
        
        # Info
        info_frame = ttk.LabelFrame(schedule, text="ℹ️ Notes", padding=15)
        info_frame.pack(fill='x', pady=10)
        
        ttk.Label(info_frame, text="• Mac must be ON at scheduled time (can be sleeping)\n• WhatsApp Desktop must be installed and logged in\n• Test with dry run before scheduling", justify='left').pack(anchor='w')
        
        # Load schedule status in background
        self.root.after(500, lambda: executor.submit(self._load_schedule_status))
    
    def create_logs_tab(self):
        """Create the logs tab."""
        logs = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(logs, text="📋 Logs")
        
        toolbar = ttk.Frame(logs)
        toolbar.pack(fill='x', pady=(0, 10))
        
        ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_logs).pack(side='left')
        ttk.Button(toolbar, text="🗑️ Clear", command=self.clear_logs).pack(side='left', padx=10)
        ttk.Button(toolbar, text="📂 Open Folder", command=self.open_logs_folder).pack(side='left', padx=10)
        
        self.log_text = scrolledtext.ScrolledText(logs, font=('Courier', 10), state='disabled')
        self.log_text.pack(fill='both', expand=True)
        
        # Load logs in background
        self.root.after(1000, lambda: executor.submit(self._load_logs))
    
    # ============= UI Update Methods (called on main thread) =============
    
    def _update_stats_ui(self):
        """Update stats display (main thread)."""
        stats = self._stats_cache
        self.stat_vars['total_contacts'].set(str(stats.get('total', 0)))
        self.stat_vars['active_contacts'].set(str(stats.get('active', 0)))
        self.stat_vars['excluded_contacts'].set(str(stats.get('excluded', 0)))
        self.stat_vars['images_count'].set(str(len(self._images_cache)))
        self.stat_vars['messaged_today'].set(str(stats.get('messaged_today', 0)))
        
        # Breakdown
        self.breakdown_text.config(state='normal')
        self.breakdown_text.delete('1.0', 'end')
        breakdown = stats.get('by_suffix', {})
        if breakdown:
            for suffix, count in breakdown.items():
                self.breakdown_text.insert('end', f"   {suffix.upper()}: {count} contacts\n")
        else:
            self.breakdown_text.insert('end', "   No contacts. Click 'Refresh Contacts' to sync.\n")
        self.breakdown_text.config(state='disabled')
    
    def _update_contacts_ui(self):
        """Update contacts treeview (main thread)."""
        self._apply_filters()
    
    def _apply_filters(self):
        """Apply filters and update treeview."""
        # Clear existing
        for item in self.contacts_tree.get_children():
            self.contacts_tree.delete(item)
        
        filter_type = self.filter_var.get()
        search_term = self.search_var.get().lower()
        
        count = 0
        for contact in self._contacts_cache:
            if filter_type != "All" and contact['suffix_type'] != filter_type:
                continue
            if search_term and search_term not in contact['name'].lower() and search_term not in contact.get('phone', ''):
                continue
            
            status = "❌ Excluded" if contact['is_excluded'] else "✅ Active"
            last_sent = contact['last_messaged'][:10] if contact.get('last_messaged') else "Never"
            
            self.contacts_tree.insert('', 'end', iid=contact['id'], values=(
                contact['name'],
                contact.get('phone', ''),
                contact['suffix_type'],
                status,
                last_sent,
                contact.get('message_count', 0)
            ))
            count += 1
        
        self.contacts_count_var.set(f"{count} contacts")
    
    def _update_images_ui(self):
        """Update images treeview (main thread)."""
        for item in self.images_tree.get_children():
            self.images_tree.delete(item)
        
        for img_path in self._images_cache:
            filename = os.path.basename(img_path)
            try:
                size = os.path.getsize(img_path)
                size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024*1024):.1f} MB"
            except:
                size_str = "—"
            self.images_tree.insert('', 'end', values=(filename, size_str))
        
        self.images_count_label.config(text=f"{len(self._images_cache)} images")
    
    # ============= Background Data Loading =============
    
    def _load_schedule_status(self):
        """Background: Load schedule status."""
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            check_status()
        output = f.getvalue()
        
        self.queue_update(self._set_schedule_text, output)
    
    def _set_schedule_text(self, text):
        """Set schedule status text (main thread)."""
        self.schedule_status_text.config(state='normal')
        self.schedule_status_text.delete('1.0', 'end')
        self.schedule_status_text.insert('end', text)
        self.schedule_status_text.config(state='disabled')
    
    def _load_logs(self):
        """Background: Load logs."""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(LOG_DIR, f"marketing_{today}.log")
        
        content = ""
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                content = f.read()
        else:
            try:
                log_files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith('.log')], reverse=True)
                if log_files:
                    with open(os.path.join(LOG_DIR, log_files[0]), 'r') as f:
                        content = f"=== {log_files[0]} ===\n\n{f.read()}"
                else:
                    content = "No logs yet. Run a campaign to generate logs."
            except:
                content = "No logs folder found."
        
        self.queue_update(self._set_log_text, content)
    
    def _set_log_text(self, text):
        """Set log text (main thread)."""
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.insert('end', text)
        self.log_text.config(state='disabled')
        self.log_text.see('end')
    
    # ============= Actions =============
    
    def refresh_contacts_action(self):
        """Refresh contacts from macOS."""
        self.status_var.set("Refreshing contacts...")
        
        def do_refresh():
            try:
                result = refresh_contacts()
                # Reload cache
                self._contacts_cache = get_all_contacts_with_status()
                self._stats_cache = get_contact_stats()
                
                self.queue_update(self._update_stats_ui)
                self.queue_update(self._update_contacts_ui)
                self.queue_update(self._show_refresh_result, result)
            except Exception as e:
                self.queue_update(messagebox.showerror, "Error", str(e))
            finally:
                self.queue_update(self.status_var.set, "Ready")
        
        executor.submit(do_refresh)
    
    def _show_refresh_result(self, result):
        """Show refresh result dialog."""
        if 'error' in result:
            messagebox.showerror("Error", result['error'])
        else:
            messagebox.showinfo("Done", f"Fetched: {result.get('fetched', 0)}\nNew: {result.get('new', 0)}\nTotal: {result.get('total', 0)}")
    
    def exclude_selected(self):
        """Exclude selected contacts."""
        selected = self.contacts_tree.selection()
        if not selected:
            return
        
        def do_exclude():
            for cid in selected:
                exclude_contact(cid)
            self._contacts_cache = get_all_contacts_with_status()
            self._stats_cache = get_contact_stats()
            self.queue_update(self._update_contacts_ui)
            self.queue_update(self._update_stats_ui)
            self.queue_update(self.status_var.set, f"Excluded {len(selected)}")
        
        executor.submit(do_exclude)
    
    def include_selected(self):
        """Include selected contacts."""
        selected = self.contacts_tree.selection()
        if not selected:
            return
        
        def do_include():
            for cid in selected:
                include_contact(cid)
            self._contacts_cache = get_all_contacts_with_status()
            self._stats_cache = get_contact_stats()
            self.queue_update(self._update_contacts_ui)
            self.queue_update(self._update_stats_ui)
            self.queue_update(self.status_var.set, f"Included {len(selected)}")
        
        executor.submit(do_include)
    
    def toggle_contact_status(self, event):
        """Toggle contact on double-click."""
        item = self.contacts_tree.selection()
        if not item:
            return
        
        contact_id = item[0]
        values = self.contacts_tree.item(contact_id, 'values')
        is_excluded = "Excluded" in values[3]
        
        def do_toggle():
            if is_excluded:
                include_contact(contact_id)
            else:
                exclude_contact(contact_id)
            self._contacts_cache = get_all_contacts_with_status()
            self._stats_cache = get_contact_stats()
            self.queue_update(self._update_contacts_ui)
            self.queue_update(self._update_stats_ui)
        
        executor.submit(do_toggle)
    
    def show_context_menu(self, event):
        """Show right-click menu."""
        try:
            self.contacts_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.contacts_menu.grab_release()
    
    def save_message(self):
        """Save message template."""
        self.config['message_template'] = self.message_text.get('1.0', 'end-1c')
        save_config(self.config)
        self.status_var.set("Message saved!")
    
    def save_settings(self):
        """Save campaign settings."""
        try:
            self.config['delay_min_seconds'] = int(self.delay_min_var.get())
            self.config['delay_max_seconds'] = int(self.delay_max_var.get())
            self.config['batch_size'] = int(self.batch_var.get())
            self.config['pause_between_batches_minutes'] = int(self.pause_var.get())
            save_config(self.config)
            self.status_var.set("Settings saved!")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
    
    def open_images_folder(self):
        """Open images folder in Finder."""
        subprocess.Popen(["open", IMAGES_DIR])
    
    def refresh_images(self):
        """Refresh images list."""
        def do_refresh():
            self._images_cache = get_marketing_images()
            self.queue_update(self._update_images_ui)
            self.queue_update(self._update_stats_ui)
        executor.submit(do_refresh)
    
    def add_images(self):
        """Add images via dialog."""
        files = filedialog.askopenfilenames(title="Select Images", filetypes=[("Images", "*.jpg *.jpeg *.png *.gif *.webp")])
        if not files:
            return
        
        def do_copy():
            import shutil
            for fp in files:
                shutil.copy2(fp, os.path.join(IMAGES_DIR, os.path.basename(fp)))
            self._images_cache = get_marketing_images()
            self.queue_update(self._update_images_ui)
            self.queue_update(self._update_stats_ui)
            self.queue_update(self.status_var.set, f"Added {len(files)} images")
        
        executor.submit(do_copy)
    
    def open_logs_folder(self):
        """Open logs folder."""
        subprocess.Popen(["open", LOG_DIR])
    
    def refresh_logs(self):
        """Refresh logs display."""
        executor.submit(self._load_logs)
    
    def clear_logs(self):
        """Clear all logs."""
        if messagebox.askyesno("Clear Logs", "Clear all logs?"):
            def do_clear():
                for f in os.listdir(LOG_DIR):
                    if f.endswith('.log'):
                        os.remove(os.path.join(LOG_DIR, f))
                self.queue_update(self._set_log_text, "Logs cleared.")
            executor.submit(do_clear)
    
    def refresh_schedule_status(self):
        """Refresh schedule status."""
        executor.submit(self._load_schedule_status)
    
    def setup_schedule_action(self):
        """Set up schedule."""
        day = self.schedule_day_var.get()
        time_str = self.schedule_time_var.get()
        
        try:
            h, m = map(int, time_str.split(':'))
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError()
        except:
            messagebox.showerror("Error", "Invalid time. Use HH:MM format.")
            return
        
        if messagebox.askyesno("Confirm", f"Schedule for {day.capitalize()} at {time_str} IST?"):
            def do_setup():
                setup_schedule(time_str, day)
                self._load_schedule_status()
                self.queue_update(messagebox.showinfo, "Success", "Schedule created!")
            executor.submit(do_setup)
    
    def remove_schedule_action(self):
        """Remove schedule."""
        if messagebox.askyesno("Confirm", "Remove schedule?"):
            def do_remove():
                unload_schedule()
                self._load_schedule_status()
            executor.submit(do_remove)
    
    def run_campaign_action(self):
        """Run campaign."""
        if not messagebox.askyesno("Confirm", f"Run campaign to {self._stats_cache.get('active', 0)} contacts?"):
            return
        
        self.status_var.set("Running campaign...")
        
        def do_run():
            try:
                result = run_marketing_campaign(dry_run=False)
                self.queue_update(self._show_campaign_result, result, False)
            except Exception as e:
                self.queue_update(messagebox.showerror, "Error", str(e))
            finally:
                self.queue_update(self.status_var.set, "Ready")
        
        executor.submit(do_run)
    
    def dry_run_action(self):
        """Dry run test."""
        self.status_var.set("Running test...")
        
        def do_test():
            try:
                result = run_marketing_campaign(dry_run=True, limit=5)
                self.queue_update(self._show_campaign_result, result, True)
            except Exception as e:
                self.queue_update(messagebox.showerror, "Error", str(e))
            finally:
                self.queue_update(self.status_var.set, "Ready")
        
        executor.submit(do_test)
    
    def _show_campaign_result(self, result, is_dry):
        """Show campaign result."""
        prefix = "[TEST] " if is_dry else ""
        messagebox.showinfo(f"{prefix}Complete", f"✅ Success: {result.get('success', 0)}\n❌ Failed: {result.get('failed', 0)}\n📋 Total: {result.get('total', 0)}")
        self._stats_cache = get_contact_stats()
        self._update_stats_ui()
        executor.submit(self._load_logs)


def main():
    root = tk.Tk()
    app = MarketingGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
