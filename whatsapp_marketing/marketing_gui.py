#!/usr/bin/env python3
"""
WhatsApp Marketing GUI - Final Optimized Version
Individual contact selection, filters, responsive UI
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
    """Run tasks in background without blocking UI."""
    
    @staticmethod
    def run(func, callback=None, error_callback=None):
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
        self.root.geometry("1300x900")
        self.root.minsize(1100, 750)
        
        # Data
        self.contacts_data = []  # All contacts from DB
        self.filtered_contacts = []  # After applying filters
        self.selected_ids = set()  # Manually selected contact IDs for sending
        self.images_data = []
        self.stats_data = {}
        
        # Config
        self.config = load_config()
        
        # Setup
        self.setup_styles()
        self.create_ui()
        
        # Load ALL contacts initially
        self.root.after(50, self.load_initial_data)
    
    def setup_styles(self):
        style = ttk.Style()
        if 'aqua' in style.theme_names():
            style.theme_use('aqua')
        
        style.configure('Title.TLabel', font=('Helvetica', 22, 'bold'))
        style.configure('Subtitle.TLabel', font=('Helvetica', 13))
        style.configure('Stat.TLabel', font=('Helvetica', 28, 'bold'))
        style.configure('StatLabel.TLabel', font=('Helvetica', 10))
        style.configure('Big.TButton', font=('Helvetica', 11), padding=6)
        style.configure('Treeview', rowheight=26, font=('Helvetica', 11))
        style.configure('Treeview.Heading', font=('Helvetica', 11, 'bold'))
        
        # Tag for selected rows
        style.map('Treeview', background=[('selected', '#0066cc')])
    
    def create_ui(self):
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
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=120)
        self.progress.pack(side='right')
    
    def show_loading(self, msg="Loading..."):
        self.status_var.set(msg)
        self.progress.start(10)
        self.root.update_idletasks()
    
    def hide_loading(self, msg="Ready"):
        self.progress.stop()
        self.status_var.set(msg)
    
    def ui_update(self, func, *args):
        """Schedule UI update on main thread."""
        self.root.after(0, lambda: func(*args))
    
    # ==================== DASHBOARD ====================
    
    def create_dashboard_tab(self):
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="📊 Dashboard")
        
        ttk.Label(tab, text="WhatsApp Marketing Dashboard", style='Title.TLabel').pack(pady=(0, 15))
        
        # Stats
        stats_frame = ttk.LabelFrame(tab, text="📈 Statistics", padding=15)
        stats_frame.pack(fill='x', pady=8)
        
        self.stat_labels = {}
        for key, label in [('total', 'Total'), ('active', 'Active'), ('excluded', 'Excluded'), ('images', 'Images'), ('today', 'Sent Today')]:
            f = ttk.Frame(stats_frame)
            f.pack(side='left', expand=True, padx=15)
            self.stat_labels[key] = tk.StringVar(value="—")
            ttk.Label(f, textvariable=self.stat_labels[key], style='Stat.TLabel').pack()
            ttk.Label(f, text=label, style='StatLabel.TLabel').pack()
        
        # Actions
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
        ttk.Label(breakdown, textvariable=self.breakdown_var, font=('Helvetica', 12), justify='left').pack(anchor='w')
    
    # ==================== CONTACTS TAB ====================
    
    def create_contacts_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="👥 Contacts")
        
        # === TOOLBAR ROW 1: Main Actions ===
        row1 = ttk.Frame(tab)
        row1.pack(fill='x', pady=4)
        
        ttk.Button(row1, text="🔄 Refresh from Mac", command=self.refresh_contacts).pack(side='left', padx=2)
        
        ttk.Separator(row1, orient='vertical').pack(side='left', fill='y', padx=8)
        
        ttk.Button(row1, text="☑️ Select All Visible", command=self.select_all).pack(side='left', padx=2)
        ttk.Button(row1, text="☐ Deselect All", command=self.deselect_all).pack(side='left', padx=2)
        ttk.Button(row1, text="🔄 Invert", command=self.invert_selection).pack(side='left', padx=2)
        
        ttk.Separator(row1, orient='vertical').pack(side='left', fill='y', padx=8)
        
        ttk.Button(row1, text="✅ Mark Included", command=self.mark_included).pack(side='left', padx=2)
        ttk.Button(row1, text="❌ Mark Excluded", command=self.mark_excluded).pack(side='left', padx=2)
        
        ttk.Separator(row1, orient='vertical').pack(side='left', fill='y', padx=8)
        
        ttk.Button(row1, text="📤 SEND TO SELECTED", command=self.send_to_selected, style='Big.TButton').pack(side='left', padx=8)
        
        # === TOOLBAR ROW 2: Filters ===
        row2 = ttk.LabelFrame(tab, text="🔍 Filters", padding=8)
        row2.pack(fill='x', pady=8)
        
        filter_row = ttk.Frame(row2)
        filter_row.pack(fill='x')
        
        # Type filter
        ttk.Label(filter_row, text="Type:").pack(side='left', padx=(0, 5))
        self.filter_type_var = tk.StringVar(value="All")
        type_combo = ttk.Combobox(filter_row, textvariable=self.filter_type_var, 
                                   values=["All", "client", "proxy", "interview"], width=10, state='readonly')
        type_combo.pack(side='left')
        type_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_filters())
        
        # Status filter
        ttk.Label(filter_row, text="Status:").pack(side='left', padx=(15, 5))
        self.filter_status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(filter_row, textvariable=self.filter_status_var,
                                     values=["All", "Included Only", "Excluded Only"], width=14, state='readonly')
        status_combo.pack(side='left')
        status_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_filters())
        
        # Custom keyword filter
        ttk.Label(filter_row, text="Keyword:").pack(side='left', padx=(15, 5))
        self.filter_keyword_var = tk.StringVar()
        keyword_entry = ttk.Entry(filter_row, textvariable=self.filter_keyword_var, width=15)
        keyword_entry.pack(side='left')
        keyword_entry.bind('<Return>', lambda e: self.apply_filters())
        
        # Search
        ttk.Label(filter_row, text="Search:").pack(side='left', padx=(15, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_row, textvariable=self.search_var, width=15)
        search_entry.pack(side='left')
        search_entry.bind('<KeyRelease>', lambda e: self.root.after(150, self.apply_filters))
        
        ttk.Button(filter_row, text="Apply", command=self.apply_filters).pack(side='left', padx=10)
        ttk.Button(filter_row, text="Clear All Filters", command=self.clear_filters).pack(side='left', padx=5)
        
        # === CONTACTS LIST ===
        list_frame = ttk.Frame(tab)
        list_frame.pack(fill='both', expand=True, pady=8)
        
        # Columns: checkbox, name, phone, type, db_status, selected_for_send, last_sent, count
        columns = ('selected', 'name', 'phone', 'type', 'db_status', 'in_send_list', 'last_sent', 'count')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', selectmode='none')
        
        self.tree.heading('selected', text='☑')
        self.tree.heading('name', text='Name')
        self.tree.heading('phone', text='Phone')
        self.tree.heading('type', text='Type')
        self.tree.heading('db_status', text='DB Status')
        self.tree.heading('in_send_list', text='Send?')
        self.tree.heading('last_sent', text='Last Sent')
        self.tree.heading('count', text='#')
        
        self.tree.column('selected', width=35, minwidth=35, anchor='center')
        self.tree.column('name', width=200, minwidth=120)
        self.tree.column('phone', width=120, minwidth=90)
        self.tree.column('type', width=70, minwidth=50)
        self.tree.column('db_status', width=90, minwidth=70, anchor='center')
        self.tree.column('in_send_list', width=60, minwidth=50, anchor='center')
        self.tree.column('last_sent', width=85, minwidth=70)
        self.tree.column('count', width=40, minwidth=35, anchor='center')
        
        # Scrollbars
        vsb = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Click to toggle selection (individual click, no range selection)
        self.tree.bind('<Button-1>', self.on_tree_click)
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        
        # Configure tags for visual feedback
        self.tree.tag_configure('selected', background='#d4edda')
        self.tree.tag_configure('excluded', foreground='#999999')
        
        # === BOTTOM INFO ===
        bottom = ttk.Frame(tab)
        bottom.pack(fill='x', pady=5)
        
        self.total_count_var = tk.StringVar(value="0 total")
        ttk.Label(bottom, textvariable=self.total_count_var, font=('Helvetica', 11)).pack(side='left')
        
        self.filtered_count_var = tk.StringVar(value="0 shown")
        ttk.Label(bottom, textvariable=self.filtered_count_var, font=('Helvetica', 11)).pack(side='left', padx=20)
        
        self.selected_count_var = tk.StringVar(value="0 selected for sending")
        ttk.Label(bottom, textvariable=self.selected_count_var, font=('Helvetica', 11, 'bold'), foreground='#007700').pack(side='left', padx=20)
        
        # Instructions
        ttk.Label(bottom, text="💡 Click = Toggle selection | Double-click = Toggle Include/Exclude in DB", 
                  font=('Helvetica', 10), foreground='#666666').pack(side='right')
    
    # ==================== MESSAGE TAB ====================
    
    def create_message_tab(self):
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="💬 Message")
        
        ttk.Label(tab, text="Message Template", style='Subtitle.TLabel').pack(anchor='w')
        
        self.message_text = scrolledtext.ScrolledText(tab, height=6, font=('Helvetica', 13), wrap='word')
        self.message_text.pack(fill='x', pady=10)
        self.message_text.insert('1.0', self.config.get('message_template', ''))
        
        ttk.Button(tab, text="💾 Save Message", command=self.save_message).pack(anchor='w', pady=5)
        
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
        ttk.Label(r2, text="    Pause:").pack(side='left')
        self.pause_var = tk.StringVar(value=str(self.config.get('pause_between_batches_minutes', 30)))
        ttk.Entry(r2, textvariable=self.pause_var, width=5).pack(side='left', padx=5)
        ttk.Label(r2, text="min").pack(side='left')
        
        ttk.Button(settings, text="💾 Save Settings", command=self.save_settings).pack(pady=10)
    
    # ==================== IMAGES TAB ====================
    
    def create_images_tab(self):
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="🖼️ Images")
        
        header = ttk.Frame(tab)
        header.pack(fill='x', pady=(0, 10))
        
        ttk.Label(header, text="Marketing Images", style='Subtitle.TLabel').pack(side='left')
        ttk.Button(header, text="🔄", command=self.refresh_images, width=3).pack(side='right')
        ttk.Button(header, text="📁 Open", command=lambda: subprocess.Popen(["open", IMAGES_DIR])).pack(side='right', padx=5)
        ttk.Button(header, text="➕ Add", command=self.add_images).pack(side='right', padx=5)
        
        ttk.Label(tab, text=f"📂 {IMAGES_DIR}", font=('Helvetica', 10)).pack(anchor='w')
        
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
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="📅 Schedule")
        
        ttk.Label(tab, text="Campaign Schedule", style='Subtitle.TLabel').pack(anchor='w', pady=(0, 15))
        
        status_frame = ttk.LabelFrame(tab, text="Current Status", padding=10)
        status_frame.pack(fill='x', pady=10)
        
        self.schedule_status_var = tk.StringVar(value="Loading...")
        ttk.Label(status_frame, textvariable=self.schedule_status_var, font=('Courier', 11)).pack(anchor='w')
        
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
        ttk.Label(row, text="IST").pack(side='left', padx=5)
        
        btn_row = ttk.Frame(config_frame)
        btn_row.pack(pady=15)
        ttk.Button(btn_row, text="✅ Set", command=self.setup_schedule, style='Big.TButton').pack(side='left', padx=10)
        ttk.Button(btn_row, text="❌ Remove", command=self.remove_schedule).pack(side='left', padx=10)
        ttk.Button(btn_row, text="🔄", command=self.refresh_schedule, width=3).pack(side='left', padx=10)
    
    # ==================== LOGS TAB ====================
    
    def create_logs_tab(self):
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="📋 Logs")
        
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill='x', pady=(0, 10))
        ttk.Button(toolbar, text="🔄", command=self.refresh_logs, width=3).pack(side='left')
        ttk.Button(toolbar, text="🗑️ Clear", command=self.clear_logs).pack(side='left', padx=10)
        ttk.Button(toolbar, text="📂 Open", command=lambda: subprocess.Popen(["open", LOG_DIR])).pack(side='left')
        
        self.log_text = scrolledtext.ScrolledText(tab, font=('Courier', 10))
        self.log_text.pack(fill='both', expand=True)
        self.log_text.insert('1.0', "Loading...")
        self.log_text.config(state='disabled')
    
    # ==================== DATA LOADING ====================
    
    def load_initial_data(self):
        """Load ALL contacts without filters."""
        self.show_loading("Loading all contacts...")
        
        def load():
            return {
                'contacts': get_all_contacts_with_status(),
                'stats': get_contact_stats(),
                'images': get_marketing_images()
            }
        
        def on_done(data):
            self.contacts_data = data['contacts']
            self.stats_data = data['stats']
            self.images_data = data['images']
            
            # Initially select all INCLUDED contacts for sending
            self.selected_ids = set(c['id'] for c in self.contacts_data if not c.get('is_excluded'))
            
            self.update_all_ui()
            self.hide_loading(f"Loaded {len(self.contacts_data)} contacts")
        
        AsyncTask.run(load, lambda d: self.ui_update(on_done, d))
    
    def update_all_ui(self):
        self.update_stats_ui()
        self.apply_filters()
        self.update_images_ui()
        self.refresh_schedule()
        self.refresh_logs()
    
    def update_stats_ui(self):
        s = self.stats_data
        self.stat_labels['total'].set(str(s.get('total', 0)))
        self.stat_labels['active'].set(str(s.get('active', 0)))
        self.stat_labels['excluded'].set(str(s.get('excluded', 0)))
        self.stat_labels['images'].set(str(len(self.images_data)))
        self.stat_labels['today'].set(str(s.get('messaged_today', 0)))
        
        by_suffix = s.get('by_suffix', {})
        if by_suffix:
            text = "\n".join([f"   {k.upper()}: {v}" for k, v in by_suffix.items()])
        else:
            text = "   No contacts. Click 'Refresh Contacts'"
        self.breakdown_var.set(text)
    
    def update_images_ui(self):
        self.images_tree.delete(*self.images_tree.get_children())
        for img in self.images_data:
            name = os.path.basename(img)
            try:
                size = os.path.getsize(img)
                size_str = f"{size/1024:.1f} KB" if size < 1048576 else f"{size/1048576:.1f} MB"
            except:
                size_str = "—"
            self.images_tree.insert('', 'end', values=(name, size_str))
        self.images_count_var.set(f"{len(self.images_data)} images (max 30)")
    
    # ==================== CONTACTS TREE ====================
    
    def apply_filters(self):
        """Apply filters and refresh the tree."""
        type_filter = self.filter_type_var.get()
        status_filter = self.filter_status_var.get()
        keyword = self.filter_keyword_var.get().lower().strip()
        search = self.search_var.get().lower().strip()
        
        self.filtered_contacts = []
        
        for c in self.contacts_data:
            # Type filter
            if type_filter != "All" and c.get('suffix_type', '') != type_filter:
                continue
            
            # Status filter
            is_excluded = c.get('is_excluded', False)
            if status_filter == "Included Only" and is_excluded:
                continue
            if status_filter == "Excluded Only" and not is_excluded:
                continue
            
            # Keyword filter (in name)
            if keyword and keyword not in c.get('name', '').lower():
                continue
            
            # Search (name or phone)
            if search:
                if search not in c.get('name', '').lower() and search not in c.get('phone', ''):
                    continue
            
            self.filtered_contacts.append(c)
        
        self.refresh_tree()
    
    def refresh_tree(self):
        """Refresh the treeview with filtered contacts."""
        self.tree.delete(*self.tree.get_children())
        
        for c in self.filtered_contacts:
            cid = c['id']
            is_selected = cid in self.selected_ids
            is_excluded = c.get('is_excluded', False)
            
            check = '☑' if is_selected else '☐'
            db_status = '❌ Excluded' if is_excluded else '✅ Included'
            send_mark = '✓' if is_selected else ''
            last_sent = c.get('last_messaged', '')[:10] if c.get('last_messaged') else "Never"
            
            tags = []
            if is_selected:
                tags.append('selected')
            if is_excluded:
                tags.append('excluded')
            
            self.tree.insert('', 'end', iid=cid, values=(
                check,
                c.get('name', ''),
                c.get('phone', ''),
                c.get('suffix_type', ''),
                db_status,
                send_mark,
                last_sent,
                c.get('message_count', 0)
            ), tags=tags)
        
        self.update_counts()
    
    def update_counts(self):
        """Update count labels."""
        self.total_count_var.set(f"{len(self.contacts_data)} total")
        self.filtered_count_var.set(f"{len(self.filtered_contacts)} shown")
        self.selected_count_var.set(f"{len(self.selected_ids)} selected for sending")
    
    def on_tree_click(self, event):
        """Handle single click - toggle selection for that specific row only."""
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        if not item:
            return
        
        # Toggle selection
        if item in self.selected_ids:
            self.selected_ids.discard(item)
        else:
            self.selected_ids.add(item)
        
        # Update just this row
        self.update_row(item)
        self.update_counts()
    
    def on_tree_double_click(self, event):
        """Handle double-click - toggle Include/Exclude in database."""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        contact = next((c for c in self.contacts_data if c['id'] == item), None)
        if not contact:
            return
        
        is_excluded = contact.get('is_excluded', False)
        
        self.show_loading("Updating...")
        
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
            self.hide_loading()
        
        AsyncTask.run(do_toggle, lambda r: self.ui_update(on_done, r))
    
    def update_row(self, item):
        """Update a single row's display."""
        contact = next((c for c in self.filtered_contacts if c['id'] == item), None)
        if not contact:
            return
        
        is_selected = item in self.selected_ids
        is_excluded = contact.get('is_excluded', False)
        
        check = '☑' if is_selected else '☐'
        send_mark = '✓' if is_selected else ''
        
        self.tree.set(item, 'selected', check)
        self.tree.set(item, 'in_send_list', send_mark)
        
        # Update tags
        tags = []
        if is_selected:
            tags.append('selected')
        if is_excluded:
            tags.append('excluded')
        self.tree.item(item, tags=tags)
    
    # ==================== SELECTION ACTIONS ====================
    
    def select_all(self):
        """Select all visible contacts."""
        for c in self.filtered_contacts:
            self.selected_ids.add(c['id'])
        self.refresh_tree()
    
    def deselect_all(self):
        """Deselect all contacts."""
        self.selected_ids.clear()
        self.refresh_tree()
    
    def invert_selection(self):
        """Invert selection for visible contacts."""
        visible_ids = set(c['id'] for c in self.filtered_contacts)
        
        # For visible contacts: toggle
        for cid in visible_ids:
            if cid in self.selected_ids:
                self.selected_ids.discard(cid)
            else:
                self.selected_ids.add(cid)
        
        self.refresh_tree()
    
    def mark_included(self):
        """Mark selected contacts as Included in database."""
        to_include = [cid for cid in self.selected_ids if any(c['id'] == cid and c.get('is_excluded') for c in self.contacts_data)]
        
        if not to_include:
            messagebox.showinfo("Info", "No excluded contacts in selection to include")
            return
        
        self.show_loading(f"Including {len(to_include)}...")
        
        def do_include():
            for cid in to_include:
                include_contact(cid)
            return get_all_contacts_with_status(), get_contact_stats()
        
        def on_done(result):
            self.contacts_data, self.stats_data = result
            self.update_stats_ui()
            self.apply_filters()
            self.hide_loading(f"Included {len(to_include)}")
        
        AsyncTask.run(do_include, lambda r: self.ui_update(on_done, r))
    
    def mark_excluded(self):
        """Mark selected contacts as Excluded in database."""
        to_exclude = [cid for cid in self.selected_ids if any(c['id'] == cid and not c.get('is_excluded') for c in self.contacts_data)]
        
        if not to_exclude:
            messagebox.showinfo("Info", "No included contacts in selection to exclude")
            return
        
        self.show_loading(f"Excluding {len(to_exclude)}...")
        
        def do_exclude():
            for cid in to_exclude:
                exclude_contact(cid)
            return get_all_contacts_with_status(), get_contact_stats()
        
        def on_done(result):
            self.contacts_data, self.stats_data = result
            # Remove excluded from send list
            for cid in to_exclude:
                self.selected_ids.discard(cid)
            self.update_stats_ui()
            self.apply_filters()
            self.hide_loading(f"Excluded {len(to_exclude)}")
        
        AsyncTask.run(do_exclude, lambda r: self.ui_update(on_done, r))
    
    def clear_filters(self):
        """Clear all filters."""
        self.filter_type_var.set("All")
        self.filter_status_var.set("All")
        self.filter_keyword_var.set("")
        self.search_var.set("")
        self.apply_filters()
    
    # ==================== CAMPAIGN ACTIONS ====================
    
    def send_to_selected(self):
        """Send to manually selected contacts."""
        if not self.selected_ids:
            messagebox.showwarning("No Selection", "No contacts selected for sending")
            return
        
        # Get active selected contacts (not excluded)
        active_selected = [c for c in self.contacts_data if c['id'] in self.selected_ids and not c.get('is_excluded')]
        
        if not active_selected:
            messagebox.showwarning("No Active", "All selected contacts are excluded from database")
            return
        
        if not messagebox.askyesno("Confirm", f"Send message to {len(active_selected)} selected contacts?"):
            return
        
        self.show_loading(f"Sending to {len(active_selected)}...")
        
        def do_send():
            self.config['message_template'] = self.message_text.get('1.0', 'end-1c')
            save_config(self.config)
            return run_marketing_campaign(dry_run=False, limit=len(active_selected))
        
        def on_done(result):
            self.hide_loading()
            messagebox.showinfo("Done", f"✅ Success: {result.get('success', 0)}\n❌ Failed: {result.get('failed', 0)}")
            self.load_initial_data()
        
        AsyncTask.run(do_send, lambda r: self.ui_update(on_done, r))
    
    def refresh_contacts(self):
        """Refresh from macOS Contacts."""
        self.show_loading("Syncing from macOS...")
        
        def do_refresh():
            result = refresh_contacts()
            contacts = get_all_contacts_with_status()
            stats = get_contact_stats()
            return result, contacts, stats
        
        def on_done(data):
            result, contacts, stats = data
            self.contacts_data = contacts
            self.stats_data = stats
            
            # Update selected_ids to only include existing contacts
            existing_ids = set(c['id'] for c in contacts)
            self.selected_ids = self.selected_ids.intersection(existing_ids)
            
            # Add new included contacts to selection
            for c in contacts:
                if not c.get('is_excluded') and c['id'] not in self.selected_ids:
                    self.selected_ids.add(c['id'])
            
            self.update_stats_ui()
            self.apply_filters()
            
            if 'error' in result:
                self.hide_loading("Error")
                messagebox.showerror("Error", result['error'])
            else:
                self.hide_loading("Synced!")
                messagebox.showinfo("Done", f"Fetched: {result.get('fetched', 0)}\nNew: {result.get('new', 0)}\nTotal: {result.get('total', 0)}")
        
        AsyncTask.run(do_refresh, lambda d: self.ui_update(on_done, d))
    
    def run_campaign(self):
        """Run full campaign to all active contacts."""
        active = self.stats_data.get('active', 0)
        if not messagebox.askyesno("Confirm", f"Send to ALL {active} included contacts?"):
            return
        
        self.show_loading("Running campaign...")
        
        def do_run():
            self.config['message_template'] = self.message_text.get('1.0', 'end-1c')
            save_config(self.config)
            return run_marketing_campaign(dry_run=False)
        
        def on_done(result):
            self.hide_loading()
            messagebox.showinfo("Done", f"✅ {result.get('success', 0)}\n❌ {result.get('failed', 0)}")
            self.load_initial_data()
        
        AsyncTask.run(do_run, lambda r: self.ui_update(on_done, r))
    
    def test_campaign(self):
        """Dry run test."""
        self.show_loading("Testing...")
        
        def do_test():
            return run_marketing_campaign(dry_run=True, limit=5)
        
        def on_done(result):
            self.hide_loading()
            messagebox.showinfo("Test", f"[DRY RUN]\nWould send to: {result.get('success', 0)}")
        
        AsyncTask.run(do_test, lambda r: self.ui_update(on_done, r))
    
    # ==================== OTHER ====================
    
    def save_message(self):
        self.config['message_template'] = self.message_text.get('1.0', 'end-1c')
        save_config(self.config)
        self.status_var.set("Message saved!")
    
    def save_settings(self):
        try:
            self.config['delay_min_seconds'] = int(self.delay_min_var.get())
            self.config['delay_max_seconds'] = int(self.delay_max_var.get())
            self.config['batch_size'] = int(self.batch_var.get())
            self.config['pause_between_batches_minutes'] = int(self.pause_var.get())
            save_config(self.config)
            self.status_var.set("Settings saved!")
        except ValueError:
            messagebox.showerror("Error", "Enter valid numbers")
    
    def refresh_images(self):
        def load():
            return get_marketing_images()
        
        def on_done(imgs):
            self.images_data = imgs
            self.update_images_ui()
            self.update_stats_ui()
        
        AsyncTask.run(load, lambda i: self.ui_update(on_done, i))
    
    def add_images(self):
        files = filedialog.askopenfilenames(title="Select Images", filetypes=[("Images", "*.jpg *.jpeg *.png *.gif *.webp")])
        if not files:
            return
        
        def do_copy():
            import shutil
            for f in files:
                shutil.copy2(f, os.path.join(IMAGES_DIR, os.path.basename(f)))
            return get_marketing_images()
        
        def on_done(imgs):
            self.images_data = imgs
            self.update_images_ui()
            self.update_stats_ui()
            self.status_var.set(f"Added {len(files)} images")
        
        AsyncTask.run(do_copy, lambda i: self.ui_update(on_done, i))
    
    def refresh_schedule(self):
        def load():
            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                check_status()
            return f.getvalue()
        
        self.ui_update(lambda t: self.schedule_status_var.set(t.strip() or "No schedule"), "")
        AsyncTask.run(load, lambda t: self.ui_update(lambda x: self.schedule_status_var.set(x.strip() or "No schedule"), t))
    
    def setup_schedule(self):
        day = self.schedule_day_var.get()
        time_str = self.schedule_time_var.get()
        
        try:
            h, m = map(int, time_str.split(':'))
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError()
        except:
            messagebox.showerror("Error", "Invalid time (use HH:MM)")
            return
        
        if messagebox.askyesno("Confirm", f"Schedule: {day.capitalize()} at {time_str}?"):
            AsyncTask.run(lambda: setup_schedule(time_str, day), lambda _: self.ui_update(self.refresh_schedule))
    
    def remove_schedule(self):
        if messagebox.askyesno("Confirm", "Remove schedule?"):
            AsyncTask.run(unload_schedule, lambda _: self.ui_update(self.refresh_schedule))
    
    def refresh_logs(self):
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
        
        AsyncTask.run(load, lambda t: self.ui_update(on_done, t))
    
    def clear_logs(self):
        if messagebox.askyesno("Clear", "Clear all logs?"):
            def do_clear():
                for f in os.listdir(LOG_DIR):
                    if f.endswith('.log'):
                        os.remove(os.path.join(LOG_DIR, f))
            AsyncTask.run(do_clear, lambda _: self.ui_update(self.refresh_logs))


def main():
    root = tk.Tk()
    app = MarketingGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
