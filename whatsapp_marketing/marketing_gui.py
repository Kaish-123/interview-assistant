#!/usr/bin/env python3
"""
WhatsApp Marketing GUI - Ultra Responsive Edition
Fast, fluid, non-blocking interface
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

from contact_fetcher import (
    refresh_contacts, get_all_contacts_with_status, get_contacts_for_messaging,
    exclude_contact, include_contact, get_contact_stats
)
from whatsapp_marketing import (
    load_config, save_config, get_marketing_images, run_marketing_campaign,
    IMAGES_DIR, LOG_DIR
)
from marketing_scheduler import setup_schedule, unload_schedule, check_status


class AsyncTask:
    """Simple async task runner that doesn't block UI."""
    
    @staticmethod
    def run(func, callback=None, error_callback=None):
        """Run function in background thread, call callback on main thread when done."""
        def wrapper():
            try:
                result = func()
                if callback:
                    callback(result)
            except Exception as e:
                if error_callback:
                    error_callback(e)
        
        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()


class MarketingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📱 WhatsApp Marketing Manager")
        self.root.geometry("1250x850")
        self.root.minsize(1000, 700)
        
        # Data cache
        self.contacts_data = []
        self.filtered_contacts = []
        self.images_data = []
        self.stats_data = {}
        
        # Prevent multiple operations
        self.is_loading = False
        
        # Config
        self.config = load_config()
        
        # Setup UI
        self.setup_styles()
        self.create_ui()
        
        # Load data after UI is ready (non-blocking)
        self.root.after(50, self.load_initial_data)
    
    def setup_styles(self):
        """Configure styles."""
        style = ttk.Style()
        if 'aqua' in style.theme_names():
            style.theme_use('aqua')
        
        style.configure('Title.TLabel', font=('SF Pro Display', 22, 'bold'))
        style.configure('Subtitle.TLabel', font=('SF Pro Display', 13))
        style.configure('Stat.TLabel', font=('SF Pro Display', 28, 'bold'))
        style.configure('StatLabel.TLabel', font=('SF Pro Display', 10))
        style.configure('Big.TButton', font=('SF Pro Display', 12), padding=8)
        style.configure('Treeview', rowheight=26, font=('SF Pro Display', 11))
        style.configure('Treeview.Heading', font=('SF Pro Display', 11, 'bold'))
    
    def create_ui(self):
        """Create the main UI."""
        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=8, pady=8)
        
        self.create_dashboard_tab()
        self.create_contacts_tab()
        self.create_message_tab()
        self.create_images_tab()
        self.create_schedule_tab()
        self.create_logs_tab()
        
        # Status bar
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill='x', padx=8, pady=4)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side='left')
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=100)
        self.progress.pack(side='right')
    
    def show_loading(self, msg="Loading..."):
        """Show loading state."""
        self.status_var.set(msg)
        self.progress.start(10)
        self.root.update_idletasks()
    
    def hide_loading(self, msg="Ready"):
        """Hide loading state."""
        self.progress.stop()
        self.status_var.set(msg)
        self.root.update_idletasks()
    
    def schedule_ui_update(self, func, *args):
        """Schedule a UI update on the main thread."""
        self.root.after(0, lambda: func(*args))
    
    # ==================== DASHBOARD TAB ====================
    
    def create_dashboard_tab(self):
        """Dashboard tab."""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="📊 Dashboard")
        
        # Title
        ttk.Label(tab, text="WhatsApp Marketing Dashboard", style='Title.TLabel').pack(pady=(0, 15))
        
        # Stats row
        stats_frame = ttk.LabelFrame(tab, text="📈 Statistics", padding=15)
        stats_frame.pack(fill='x', pady=8)
        
        self.stat_labels = {}
        stats = [('total', 'Total'), ('active', 'Active'), ('excluded', 'Excluded'), ('images', 'Images'), ('today', 'Sent Today')]
        
        for key, label in stats:
            f = ttk.Frame(stats_frame)
            f.pack(side='left', expand=True, padx=15)
            self.stat_labels[key] = tk.StringVar(value="—")
            ttk.Label(f, textvariable=self.stat_labels[key], style='Stat.TLabel').pack()
            ttk.Label(f, text=label, style='StatLabel.TLabel').pack()
        
        # Quick actions
        actions = ttk.LabelFrame(tab, text="⚡ Quick Actions", padding=15)
        actions.pack(fill='x', pady=15)
        
        btn_row = ttk.Frame(actions)
        btn_row.pack()
        
        ttk.Button(btn_row, text="🔄 Refresh Contacts", command=self.refresh_contacts, style='Big.TButton').pack(side='left', padx=8)
        ttk.Button(btn_row, text="🚀 Run Campaign", command=self.run_campaign, style='Big.TButton').pack(side='left', padx=8)
        ttk.Button(btn_row, text="🧪 Test Run", command=self.test_campaign, style='Big.TButton').pack(side='left', padx=8)
        ttk.Button(btn_row, text="📁 Images Folder", command=lambda: subprocess.Popen(["open", IMAGES_DIR]), style='Big.TButton').pack(side='left', padx=8)
        
        # Breakdown
        breakdown = ttk.LabelFrame(tab, text="📋 Contact Breakdown", padding=15)
        breakdown.pack(fill='both', expand=True, pady=8)
        
        self.breakdown_var = tk.StringVar(value="Loading...")
        ttk.Label(breakdown, textvariable=self.breakdown_var, font=('SF Pro Display', 12), justify='left').pack(anchor='w')
    
    # ==================== CONTACTS TAB ====================
    
    def create_contacts_tab(self):
        """Contacts management tab with Select All, filters, etc."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="👥 Contacts")
        
        # === TOP TOOLBAR ===
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill='x', pady=(0, 8))
        
        # Row 1: Main actions
        row1 = ttk.Frame(toolbar)
        row1.pack(fill='x', pady=2)
        
        ttk.Button(row1, text="🔄 Refresh from Mac", command=self.refresh_contacts).pack(side='left', padx=2)
        ttk.Button(row1, text="📥 Import Contacts", command=self.import_contacts).pack(side='left', padx=2)
        
        ttk.Separator(row1, orient='vertical').pack(side='left', fill='y', padx=10)
        
        ttk.Button(row1, text="☑️ Select All", command=self.select_all_contacts).pack(side='left', padx=2)
        ttk.Button(row1, text="☐ Deselect All", command=self.deselect_all_contacts).pack(side='left', padx=2)
        ttk.Button(row1, text="🔄 Invert Selection", command=self.invert_selection).pack(side='left', padx=2)
        
        ttk.Separator(row1, orient='vertical').pack(side='left', fill='y', padx=10)
        
        ttk.Button(row1, text="✅ Include Selected", command=self.include_selected).pack(side='left', padx=2)
        ttk.Button(row1, text="❌ Exclude Selected", command=self.exclude_selected).pack(side='left', padx=2)
        
        ttk.Separator(row1, orient='vertical').pack(side='left', fill='y', padx=10)
        
        ttk.Button(row1, text="📤 Send to Selected", command=self.send_to_selected, style='Big.TButton').pack(side='left', padx=5)
        
        # Row 2: Filters
        row2 = ttk.Frame(toolbar)
        row2.pack(fill='x', pady=6)
        
        ttk.Label(row2, text="Filter Type:").pack(side='left', padx=(0, 5))
        self.filter_type_var = tk.StringVar(value="All")
        type_combo = ttk.Combobox(row2, textvariable=self.filter_type_var, 
                                   values=["All", "client", "proxy", "interview"], 
                                   width=12, state='readonly')
        type_combo.pack(side='left')
        type_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_filters())
        
        ttk.Label(row2, text="Custom Filter:").pack(side='left', padx=(20, 5))
        self.custom_filter_var = tk.StringVar()
        custom_entry = ttk.Entry(row2, textvariable=self.custom_filter_var, width=20)
        custom_entry.pack(side='left')
        custom_entry.bind('<Return>', lambda e: self.apply_filters())
        ttk.Button(row2, text="Apply", command=self.apply_filters).pack(side='left', padx=5)
        
        ttk.Label(row2, text="Search:").pack(side='left', padx=(20, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(row2, textvariable=self.search_var, width=20)
        search_entry.pack(side='left')
        search_entry.bind('<KeyRelease>', lambda e: self.root.after(100, self.apply_filters))
        
        ttk.Button(row2, text="Clear Filters", command=self.clear_filters).pack(side='left', padx=10)
        
        # Row 3: Status filter
        row3 = ttk.Frame(toolbar)
        row3.pack(fill='x', pady=2)
        
        ttk.Label(row3, text="Show:").pack(side='left', padx=(0, 5))
        self.status_filter_var = tk.StringVar(value="All")
        for val in ["All", "Active Only", "Excluded Only"]:
            ttk.Radiobutton(row3, text=val, variable=self.status_filter_var, value=val, 
                           command=self.apply_filters).pack(side='left', padx=5)
        
        # === CONTACTS TREEVIEW ===
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill='both', expand=True)
        
        columns = ('select', 'name', 'phone', 'type', 'status', 'last_sent', 'count')
        self.contacts_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode='extended')
        
        self.contacts_tree.heading('select', text='✓')
        self.contacts_tree.heading('name', text='Name')
        self.contacts_tree.heading('phone', text='Phone')
        self.contacts_tree.heading('type', text='Type')
        self.contacts_tree.heading('status', text='Status')
        self.contacts_tree.heading('last_sent', text='Last Sent')
        self.contacts_tree.heading('count', text='Count')
        
        self.contacts_tree.column('select', width=40, minwidth=40, anchor='center')
        self.contacts_tree.column('name', width=220, minwidth=150)
        self.contacts_tree.column('phone', width=130, minwidth=100)
        self.contacts_tree.column('type', width=80, minwidth=60)
        self.contacts_tree.column('status', width=90, minwidth=70)
        self.contacts_tree.column('last_sent', width=90, minwidth=70)
        self.contacts_tree.column('count', width=50, minwidth=40)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=self.contacts_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.contacts_tree.xview)
        self.contacts_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.contacts_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bindings
        self.contacts_tree.bind('<Double-1>', self.toggle_contact)
        self.contacts_tree.bind('<space>', self.toggle_selected_contacts)
        
        # Bottom info
        bottom = ttk.Frame(tab)
        bottom.pack(fill='x', pady=5)
        
        self.contacts_count_var = tk.StringVar(value="0 contacts")
        ttk.Label(bottom, textvariable=self.contacts_count_var, font=('SF Pro Display', 11)).pack(side='left')
        
        self.selected_count_var = tk.StringVar(value="0 selected")
        ttk.Label(bottom, textvariable=self.selected_count_var, font=('SF Pro Display', 11, 'bold')).pack(side='left', padx=20)
        
        # Update selected count on selection change
        self.contacts_tree.bind('<<TreeviewSelect>>', lambda e: self.update_selected_count())
    
    # ==================== MESSAGE TAB ====================
    
    def create_message_tab(self):
        """Message template tab."""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="💬 Message")
        
        ttk.Label(tab, text="Message Template", style='Subtitle.TLabel').pack(anchor='w')
        
        self.message_text = scrolledtext.ScrolledText(tab, height=6, font=('SF Pro Display', 13), wrap='word')
        self.message_text.pack(fill='x', pady=10)
        self.message_text.insert('1.0', self.config.get('message_template', ''))
        
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(anchor='w', pady=5)
        ttk.Button(btn_frame, text="💾 Save Message", command=self.save_message).pack(side='left')
        ttk.Label(btn_frame, text="   ✓ Auto-saved when you run campaign", font=('SF Pro Display', 10)).pack(side='left')
        
        # Settings
        settings = ttk.LabelFrame(tab, text="⚙️ Campaign Settings", padding=15)
        settings.pack(fill='x', pady=15)
        
        r1 = ttk.Frame(settings)
        r1.pack(fill='x', pady=5)
        ttk.Label(r1, text="Delay between messages:").pack(side='left')
        self.delay_min_var = tk.StringVar(value=str(self.config.get('delay_min_seconds', 45)))
        self.delay_max_var = tk.StringVar(value=str(self.config.get('delay_max_seconds', 120)))
        ttk.Entry(r1, textvariable=self.delay_min_var, width=5).pack(side='left', padx=5)
        ttk.Label(r1, text="to").pack(side='left')
        ttk.Entry(r1, textvariable=self.delay_max_var, width=5).pack(side='left', padx=5)
        ttk.Label(r1, text="seconds").pack(side='left')
        
        r2 = ttk.Frame(settings)
        r2.pack(fill='x', pady=5)
        ttk.Label(r2, text="Batch size:").pack(side='left')
        self.batch_var = tk.StringVar(value=str(self.config.get('batch_size', 50)))
        ttk.Entry(r2, textvariable=self.batch_var, width=5).pack(side='left', padx=5)
        ttk.Label(r2, text="    Pause between batches:").pack(side='left')
        self.pause_var = tk.StringVar(value=str(self.config.get('pause_between_batches_minutes', 30)))
        ttk.Entry(r2, textvariable=self.pause_var, width=5).pack(side='left', padx=5)
        ttk.Label(r2, text="minutes").pack(side='left')
        
        ttk.Button(settings, text="💾 Save Settings", command=self.save_settings).pack(pady=10)
    
    # ==================== IMAGES TAB ====================
    
    def create_images_tab(self):
        """Images tab."""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="🖼️ Images")
        
        header = ttk.Frame(tab)
        header.pack(fill='x', pady=(0, 10))
        
        ttk.Label(header, text="Marketing Images", style='Subtitle.TLabel').pack(side='left')
        ttk.Button(header, text="🔄 Refresh", command=self.refresh_images).pack(side='right')
        ttk.Button(header, text="📁 Open Folder", command=lambda: subprocess.Popen(["open", IMAGES_DIR])).pack(side='right', padx=5)
        ttk.Button(header, text="➕ Add Images", command=self.add_images).pack(side='right', padx=5)
        
        ttk.Label(tab, text=f"📂 {IMAGES_DIR}", font=('SF Pro Display', 10)).pack(anchor='w')
        
        # Images list
        list_frame = ttk.Frame(tab)
        list_frame.pack(fill='both', expand=True, pady=10)
        
        self.images_tree = ttk.Treeview(list_frame, columns=('filename', 'size'), show='headings')
        self.images_tree.heading('filename', text='Filename')
        self.images_tree.heading('size', text='Size')
        self.images_tree.column('filename', width=400)
        self.images_tree.column('size', width=100)
        
        vsb = ttk.Scrollbar(list_frame, orient='vertical', command=self.images_tree.yview)
        self.images_tree.configure(yscrollcommand=vsb.set)
        self.images_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        
        self.images_count_var = tk.StringVar(value="0 images")
        ttk.Label(tab, textvariable=self.images_count_var).pack(anchor='w')
    
    # ==================== SCHEDULE TAB ====================
    
    def create_schedule_tab(self):
        """Schedule tab."""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="📅 Schedule")
        
        ttk.Label(tab, text="Campaign Schedule", style='Subtitle.TLabel').pack(anchor='w', pady=(0, 15))
        
        # Status
        status_frame = ttk.LabelFrame(tab, text="Current Status", padding=10)
        status_frame.pack(fill='x', pady=10)
        
        self.schedule_status_var = tk.StringVar(value="Loading...")
        ttk.Label(status_frame, textvariable=self.schedule_status_var, font=('Courier', 11)).pack(anchor='w')
        
        # Configure
        config_frame = ttk.LabelFrame(tab, text="⚙️ Configure", padding=15)
        config_frame.pack(fill='x', pady=15)
        
        row = ttk.Frame(config_frame)
        row.pack(fill='x', pady=5)
        
        ttk.Label(row, text="Day:").pack(side='left')
        self.schedule_day_var = tk.StringVar(value="saturday")
        ttk.Combobox(row, textvariable=self.schedule_day_var, 
                     values=["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
                     width=12, state='readonly').pack(side='left', padx=10)
        
        ttk.Label(row, text="Time:").pack(side='left', padx=(20, 5))
        self.schedule_time_var = tk.StringVar(value="02:00")
        ttk.Entry(row, textvariable=self.schedule_time_var, width=8).pack(side='left')
        ttk.Label(row, text="IST (24hr)").pack(side='left', padx=5)
        
        btn_row = ttk.Frame(config_frame)
        btn_row.pack(pady=15)
        ttk.Button(btn_row, text="✅ Set Schedule", command=self.setup_schedule, style='Big.TButton').pack(side='left', padx=10)
        ttk.Button(btn_row, text="❌ Remove", command=self.remove_schedule).pack(side='left', padx=10)
        ttk.Button(btn_row, text="🔄 Refresh", command=self.refresh_schedule).pack(side='left', padx=10)
    
    # ==================== LOGS TAB ====================
    
    def create_logs_tab(self):
        """Logs tab."""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="📋 Logs")
        
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill='x', pady=(0, 10))
        ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_logs).pack(side='left')
        ttk.Button(toolbar, text="🗑️ Clear", command=self.clear_logs).pack(side='left', padx=10)
        ttk.Button(toolbar, text="📂 Open Folder", command=lambda: subprocess.Popen(["open", LOG_DIR])).pack(side='left')
        
        self.log_text = scrolledtext.ScrolledText(tab, font=('Courier', 10))
        self.log_text.pack(fill='both', expand=True)
        self.log_text.insert('1.0', "Loading logs...")
        self.log_text.config(state='disabled')
    
    # ==================== DATA LOADING ====================
    
    def load_initial_data(self):
        """Load all data in background."""
        self.show_loading("Loading data...")
        
        def load():
            data = {
                'contacts': get_all_contacts_with_status(),
                'stats': get_contact_stats(),
                'images': get_marketing_images()
            }
            return data
        
        def on_done(data):
            self.contacts_data = data['contacts']
            self.stats_data = data['stats']
            self.images_data = data['images']
            self.update_all_ui()
            self.hide_loading()
        
        AsyncTask.run(load, lambda d: self.schedule_ui_update(on_done, d))
    
    def update_all_ui(self):
        """Update all UI elements with cached data."""
        self.update_stats_ui()
        self.apply_filters()
        self.update_images_ui()
        self.refresh_schedule()
        self.refresh_logs()
    
    def update_stats_ui(self):
        """Update dashboard stats."""
        s = self.stats_data
        self.stat_labels['total'].set(str(s.get('total', 0)))
        self.stat_labels['active'].set(str(s.get('active', 0)))
        self.stat_labels['excluded'].set(str(s.get('excluded', 0)))
        self.stat_labels['images'].set(str(len(self.images_data)))
        self.stat_labels['today'].set(str(s.get('messaged_today', 0)))
        
        # Breakdown
        by_suffix = s.get('by_suffix', {})
        if by_suffix:
            text = "\n".join([f"   {k.upper()}: {v} contacts" for k, v in by_suffix.items()])
        else:
            text = "   No contacts found. Click 'Refresh Contacts' to sync from macOS."
        self.breakdown_var.set(text)
    
    def update_images_ui(self):
        """Update images list."""
        self.images_tree.delete(*self.images_tree.get_children())
        for img in self.images_data:
            name = os.path.basename(img)
            try:
                size = os.path.getsize(img)
                size_str = f"{size/1024:.1f} KB" if size < 1048576 else f"{size/1048576:.1f} MB"
            except:
                size_str = "—"
            self.images_tree.insert('', 'end', values=(name, size_str))
        self.images_count_var.set(f"{len(self.images_data)} images (max 30 per message)")
    
    # ==================== CONTACTS ACTIONS ====================
    
    def apply_filters(self):
        """Apply all filters and update contacts tree."""
        # Get filter values
        type_filter = self.filter_type_var.get()
        custom_filter = self.custom_filter_var.get().lower().strip()
        search = self.search_var.get().lower().strip()
        status_filter = self.status_filter_var.get()
        
        # Filter contacts
        self.filtered_contacts = []
        for c in self.contacts_data:
            # Type filter
            if type_filter != "All" and c.get('suffix_type', '') != type_filter:
                continue
            
            # Custom filter (in name)
            if custom_filter and custom_filter not in c.get('name', '').lower():
                continue
            
            # Search (name or phone)
            if search:
                if search not in c.get('name', '').lower() and search not in c.get('phone', ''):
                    continue
            
            # Status filter
            is_excluded = c.get('is_excluded', False)
            if status_filter == "Active Only" and is_excluded:
                continue
            if status_filter == "Excluded Only" and not is_excluded:
                continue
            
            self.filtered_contacts.append(c)
        
        # Update treeview
        self.contacts_tree.delete(*self.contacts_tree.get_children())
        
        for c in self.filtered_contacts:
            status = "❌ Excluded" if c.get('is_excluded') else "✅ Active"
            last_sent = c.get('last_messaged', '')[:10] if c.get('last_messaged') else "Never"
            
            self.contacts_tree.insert('', 'end', iid=c['id'], values=(
                '☐',
                c.get('name', ''),
                c.get('phone', ''),
                c.get('suffix_type', ''),
                status,
                last_sent,
                c.get('message_count', 0)
            ))
        
        self.contacts_count_var.set(f"{len(self.filtered_contacts)} contacts shown")
        self.update_selected_count()
    
    def clear_filters(self):
        """Clear all filters."""
        self.filter_type_var.set("All")
        self.custom_filter_var.set("")
        self.search_var.set("")
        self.status_filter_var.set("All")
        self.apply_filters()
    
    def select_all_contacts(self):
        """Select all visible contacts."""
        items = self.contacts_tree.get_children()
        self.contacts_tree.selection_set(items)
        for item in items:
            self.contacts_tree.set(item, 'select', '☑')
        self.update_selected_count()
    
    def deselect_all_contacts(self):
        """Deselect all contacts."""
        self.contacts_tree.selection_remove(self.contacts_tree.selection())
        for item in self.contacts_tree.get_children():
            self.contacts_tree.set(item, 'select', '☐')
        self.update_selected_count()
    
    def invert_selection(self):
        """Invert current selection."""
        all_items = set(self.contacts_tree.get_children())
        selected = set(self.contacts_tree.selection())
        new_selection = all_items - selected
        
        self.contacts_tree.selection_set(list(new_selection))
        for item in all_items:
            self.contacts_tree.set(item, 'select', '☑' if item in new_selection else '☐')
        self.update_selected_count()
    
    def update_selected_count(self):
        """Update selected count display."""
        count = len(self.contacts_tree.selection())
        self.selected_count_var.set(f"{count} selected")
    
    def toggle_contact(self, event):
        """Toggle contact on double-click."""
        item = self.contacts_tree.identify_row(event.y)
        if not item:
            return
        
        # Find contact
        contact = next((c for c in self.contacts_data if c['id'] == item), None)
        if not contact:
            return
        
        is_excluded = contact.get('is_excluded', False)
        
        def do_toggle():
            if is_excluded:
                include_contact(item)
            else:
                exclude_contact(item)
            return get_all_contacts_with_status(), get_contact_stats()
        
        def on_done(result):
            self.contacts_data, self.stats_data = result
            self.update_stats_ui()
            self.apply_filters()
        
        AsyncTask.run(do_toggle, lambda r: self.schedule_ui_update(on_done, r))
    
    def toggle_selected_contacts(self, event):
        """Toggle selection with spacebar."""
        selected = self.contacts_tree.selection()
        for item in selected:
            current = self.contacts_tree.set(item, 'select')
            self.contacts_tree.set(item, 'select', '☐' if current == '☑' else '☑')
    
    def include_selected(self):
        """Include selected contacts."""
        selected = list(self.contacts_tree.selection())
        if not selected:
            return
        
        self.show_loading(f"Including {len(selected)} contacts...")
        
        def do_include():
            for cid in selected:
                include_contact(cid)
            return get_all_contacts_with_status(), get_contact_stats()
        
        def on_done(result):
            self.contacts_data, self.stats_data = result
            self.update_stats_ui()
            self.apply_filters()
            self.hide_loading(f"Included {len(selected)} contacts")
        
        AsyncTask.run(do_include, lambda r: self.schedule_ui_update(on_done, r))
    
    def exclude_selected(self):
        """Exclude selected contacts."""
        selected = list(self.contacts_tree.selection())
        if not selected:
            return
        
        self.show_loading(f"Excluding {len(selected)} contacts...")
        
        def do_exclude():
            for cid in selected:
                exclude_contact(cid)
            return get_all_contacts_with_status(), get_contact_stats()
        
        def on_done(result):
            self.contacts_data, self.stats_data = result
            self.update_stats_ui()
            self.apply_filters()
            self.hide_loading(f"Excluded {len(selected)} contacts")
        
        AsyncTask.run(do_exclude, lambda r: self.schedule_ui_update(on_done, r))
    
    def refresh_contacts(self):
        """Refresh contacts from macOS."""
        self.show_loading("Refreshing contacts from macOS...")
        
        def do_refresh():
            result = refresh_contacts()
            contacts = get_all_contacts_with_status()
            stats = get_contact_stats()
            return result, contacts, stats
        
        def on_done(data):
            result, contacts, stats = data
            self.contacts_data = contacts
            self.stats_data = stats
            self.update_stats_ui()
            self.apply_filters()
            
            if 'error' in result:
                self.hide_loading("Error")
                messagebox.showerror("Error", result['error'])
            else:
                self.hide_loading("Contacts refreshed!")
                messagebox.showinfo("Done", f"Fetched: {result.get('fetched', 0)}\nNew: {result.get('new', 0)}\nTotal: {result.get('total', 0)}")
        
        AsyncTask.run(do_refresh, lambda d: self.schedule_ui_update(on_done, d))
    
    def import_contacts(self):
        """Import contacts from CSV/VCF file."""
        file_path = filedialog.askopenfilename(
            title="Select Contacts File",
            filetypes=[("CSV files", "*.csv"), ("VCF files", "*.vcf"), ("All files", "*.*")]
        )
        if file_path:
            messagebox.showinfo("Import", f"Import from {os.path.basename(file_path)} not yet implemented.\n\nFor now, sync contacts via iCloud:\n1. Add contacts to iPhone\n2. Sync via iCloud to Mac\n3. Click 'Refresh from Mac'")
    
    def send_to_selected(self):
        """Send campaign to selected contacts only."""
        selected = list(self.contacts_tree.selection())
        if not selected:
            messagebox.showwarning("No Selection", "Please select contacts to send to")
            return
        
        # Get selected contact details
        selected_contacts = [c for c in self.filtered_contacts if c['id'] in selected and not c.get('is_excluded')]
        
        if not selected_contacts:
            messagebox.showwarning("No Active Contacts", "All selected contacts are excluded")
            return
        
        if not messagebox.askyesno("Confirm", f"Send to {len(selected_contacts)} selected contacts?"):
            return
        
        self.show_loading(f"Sending to {len(selected_contacts)} contacts...")
        
        def do_send():
            # Save message first
            self.config['message_template'] = self.message_text.get('1.0', 'end-1c')
            save_config(self.config)
            
            # Run campaign with selected contacts
            result = run_marketing_campaign(dry_run=False, limit=len(selected_contacts))
            return result
        
        def on_done(result):
            self.hide_loading()
            messagebox.showinfo("Complete", f"✅ Success: {result.get('success', 0)}\n❌ Failed: {result.get('failed', 0)}")
            self.load_initial_data()
        
        AsyncTask.run(do_send, lambda r: self.schedule_ui_update(on_done, r))
    
    # ==================== OTHER ACTIONS ====================
    
    def save_message(self):
        """Save message template."""
        self.config['message_template'] = self.message_text.get('1.0', 'end-1c')
        save_config(self.config)
        self.status_var.set("Message saved!")
    
    def save_settings(self):
        """Save settings."""
        try:
            self.config['delay_min_seconds'] = int(self.delay_min_var.get())
            self.config['delay_max_seconds'] = int(self.delay_max_var.get())
            self.config['batch_size'] = int(self.batch_var.get())
            self.config['pause_between_batches_minutes'] = int(self.pause_var.get())
            save_config(self.config)
            self.status_var.set("Settings saved!")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
    
    def refresh_images(self):
        """Refresh images list."""
        def load():
            return get_marketing_images()
        
        def on_done(images):
            self.images_data = images
            self.update_images_ui()
            self.update_stats_ui()
        
        AsyncTask.run(load, lambda i: self.schedule_ui_update(on_done, i))
    
    def add_images(self):
        """Add images."""
        files = filedialog.askopenfilenames(title="Select Images", filetypes=[("Images", "*.jpg *.jpeg *.png *.gif *.webp")])
        if not files:
            return
        
        def do_copy():
            import shutil
            for f in files:
                shutil.copy2(f, os.path.join(IMAGES_DIR, os.path.basename(f)))
            return get_marketing_images()
        
        def on_done(images):
            self.images_data = images
            self.update_images_ui()
            self.update_stats_ui()
            self.status_var.set(f"Added {len(files)} images")
        
        AsyncTask.run(do_copy, lambda i: self.schedule_ui_update(on_done, i))
    
    def refresh_schedule(self):
        """Refresh schedule status."""
        def load():
            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                check_status()
            return f.getvalue()
        
        def on_done(text):
            self.schedule_status_var.set(text.strip() or "No schedule set")
        
        AsyncTask.run(load, lambda t: self.schedule_ui_update(on_done, t))
    
    def setup_schedule(self):
        """Set up schedule."""
        day = self.schedule_day_var.get()
        time_str = self.schedule_time_var.get()
        
        try:
            h, m = map(int, time_str.split(':'))
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError()
        except:
            messagebox.showerror("Error", "Invalid time format (use HH:MM)")
            return
        
        if messagebox.askyesno("Confirm", f"Schedule for {day.capitalize()} at {time_str} IST?"):
            def do_setup():
                setup_schedule(time_str, day)
            
            AsyncTask.run(do_setup, lambda _: self.schedule_ui_update(self.refresh_schedule))
    
    def remove_schedule(self):
        """Remove schedule."""
        if messagebox.askyesno("Confirm", "Remove schedule?"):
            AsyncTask.run(unload_schedule, lambda _: self.schedule_ui_update(self.refresh_schedule))
    
    def refresh_logs(self):
        """Refresh logs."""
        def load():
            today = datetime.now().strftime('%Y-%m-%d')
            log_file = os.path.join(LOG_DIR, f"marketing_{today}.log")
            
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    return f.read()
            
            try:
                files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith('.log')], reverse=True)
                if files:
                    with open(os.path.join(LOG_DIR, files[0]), 'r') as f:
                        return f"=== {files[0]} ===\n\n{f.read()}"
            except:
                pass
            return "No logs yet."
        
        def on_done(text):
            self.log_text.config(state='normal')
            self.log_text.delete('1.0', 'end')
            self.log_text.insert('1.0', text)
            self.log_text.config(state='disabled')
            self.log_text.see('end')
        
        AsyncTask.run(load, lambda t: self.schedule_ui_update(on_done, t))
    
    def clear_logs(self):
        """Clear logs."""
        if messagebox.askyesno("Clear", "Clear all logs?"):
            def do_clear():
                for f in os.listdir(LOG_DIR):
                    if f.endswith('.log'):
                        os.remove(os.path.join(LOG_DIR, f))
            
            AsyncTask.run(do_clear, lambda _: self.schedule_ui_update(self.refresh_logs))
    
    def run_campaign(self):
        """Run full campaign."""
        active = self.stats_data.get('active', 0)
        if not messagebox.askyesno("Confirm", f"Run campaign to ALL {active} active contacts?\n\nThis may take several hours."):
            return
        
        self.show_loading("Running campaign...")
        
        def do_run():
            self.config['message_template'] = self.message_text.get('1.0', 'end-1c')
            save_config(self.config)
            return run_marketing_campaign(dry_run=False)
        
        def on_done(result):
            self.hide_loading()
            messagebox.showinfo("Complete", f"✅ Success: {result.get('success', 0)}\n❌ Failed: {result.get('failed', 0)}\n📋 Total: {result.get('total', 0)}")
            self.load_initial_data()
        
        AsyncTask.run(do_run, lambda r: self.schedule_ui_update(on_done, r))
    
    def test_campaign(self):
        """Test campaign (dry run)."""
        self.show_loading("Running test...")
        
        def do_test():
            return run_marketing_campaign(dry_run=True, limit=5)
        
        def on_done(result):
            self.hide_loading()
            messagebox.showinfo("Test Complete", f"[DRY RUN]\n✅ Would send to: {result.get('success', 0)}\n❌ Failed: {result.get('failed', 0)}")
        
        AsyncTask.run(do_test, lambda r: self.schedule_ui_update(on_done, r))


def main():
    root = tk.Tk()
    app = MarketingGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
