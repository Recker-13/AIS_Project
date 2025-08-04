import ttkbootstrap as tb
from ttkbootstrap.constants import *
import sqlite3
import os
from ttkbootstrap.dialogs import Messagebox
import datetime
import random
import string

DB_NAME = 'ais.db'

# Database setup

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Chart of Accounts
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL
    )''')
    
    # Initialize default accounts if they don't exist
    default_accounts = [
        ('Cash', 'Asset'),
        ('Bank', 'Asset'),
        ('Accounts Receivable', 'Asset'),
        ('Inventory', 'Asset'),
        ('Equipment', 'Asset'),
        ('Accounts Payable', 'Liability'),
        ('Sales Revenue', 'Income'),
        ('Cost of Goods Sold', 'Expense'),
        ('Operating Expenses', 'Expense'),
        ('Payroll Expense', 'Expense'),
        ('Capital', 'Equity'),
        ('Retained Earnings', 'Equity'),
        ('Inventory Adjustment', 'Equity')
    ]
    
    for name, acc_type in default_accounts:
        c.execute('SELECT id FROM accounts WHERE name = ?', (name,))
        if not c.fetchone():
            c.execute('INSERT INTO accounts (name, type) VALUES (?, ?)', (name, acc_type))
    
    # Journal Entries
    c.execute('''CREATE TABLE IF NOT EXISTS journal_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        description TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS journal_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_id INTEGER,
        account_id INTEGER,
        debit REAL,
        credit REAL,
        FOREIGN KEY(entry_id) REFERENCES journal_entries(id),
        FOREIGN KEY(account_id) REFERENCES accounts(id)
    )''')
    # Restaurant Menu Items
    c.execute('''CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        category TEXT,
        preparation_time INTEGER,
        is_available INTEGER DEFAULT 1
    )''')
    # Restaurant Orders
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT NOT NULL,
        table_number INTEGER,
        order_date TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        total_amount REAL,
        cost_amount REAL,
        payment_status TEXT DEFAULT 'unpaid',
        payment_method TEXT,
        cashier_id INTEGER,
        FOREIGN KEY(cashier_id) REFERENCES users(id)
    )''')
    # Order Items
    c.execute('''CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        menu_item_id INTEGER,
        quantity INTEGER,
        price REAL,
        status TEXT DEFAULT 'pending',
        notes TEXT,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(menu_item_id) REFERENCES menu_items(id)
    )''')
    # Restaurant Tables
    c.execute('''CREATE TABLE IF NOT EXISTS tables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_number INTEGER UNIQUE,
        capacity INTEGER,
        status TEXT DEFAULT 'available'
    )''')
    # Restaurant Users (Staff)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        name TEXT,
        is_active INTEGER DEFAULT 1
    )''')
    # Kitchen Inventory
    c.execute('''CREATE TABLE IF NOT EXISTS kitchen_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity REAL,
        unit TEXT,
        reorder_level REAL,
        cost_per_unit REAL
    )''')
    # Menu Item Ingredients
    c.execute('''CREATE TABLE IF NOT EXISTS menu_item_ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        menu_item_id INTEGER,
        inventory_id INTEGER,
        quantity REAL,
        FOREIGN KEY(menu_item_id) REFERENCES menu_items(id),
        FOREIGN KEY(inventory_id) REFERENCES kitchen_inventory(id)
    )''')
    # AR/AP (Receivables/Payables)
    c.execute('''CREATE TABLE IF NOT EXISTS receivables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT,
        amount REAL,
        due_date TEXT,
        paid INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS payables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor TEXT,
        amount REAL,
        due_date TEXT,
        paid INTEGER DEFAULT 0
    )''')
    # Customers
    c.execute('''CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact TEXT
    )''')
    # Suppliers
    c.execute('''CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact TEXT
    )''')
    # Inventory
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sku TEXT,
        quantity INTEGER DEFAULT 0,
        cost REAL,
        price REAL
    )''')
    # Purchases
    c.execute('''CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        supplier_id INTEGER,
        total REAL,
        FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS purchase_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        purchase_id INTEGER,
        inventory_id INTEGER,
        quantity INTEGER,
        cost REAL,
        FOREIGN KEY(purchase_id) REFERENCES purchases(id),
        FOREIGN KEY(inventory_id) REFERENCES inventory(id)
    )''')
    # Expenses
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        type TEXT,
        amount REAL,
        description TEXT
    )''')
    conn.commit()
    conn.close()

class AISApp(tb.Window):
    def __init__(self):
        super().__init__(themename='flatly')
        self.title('Restaurant Accounting Information System')
        self.geometry('1050x750')
        self.create_widgets()

    def create_widgets(self):
        # App Title with a colored header
        title_frame = tb.Frame(self, bootstyle='primary')
        title_frame.pack(fill='x', pady=(0, 10))
        tb.Label(title_frame, text='Restaurant Accounting Information System', font=('Segoe UI', 22, 'bold'), bootstyle='inverse-primary').pack(pady=18)

        # Create main container frame
        main_container = tb.Frame(self)
        main_container.pack(expand=1, fill='both', padx=20, pady=20)

        # Create notebook for tabs
        tab_control = tb.Notebook(main_container, bootstyle='primary')
        tab_control.pack(expand=1, fill='both')

        # Group 1: Restaurant Operations
        restaurant_frame = tb.Frame(tab_control)
        tab_control.add(restaurant_frame, text='Restaurant Operations')
        restaurant_tabs = tb.Notebook(restaurant_frame)
        restaurant_tabs.pack(expand=1, fill='both', padx=5, pady=5)
        self.tabs = {}
        
        # Restaurant-specific tabs
        for tab_name in ['Menu', 'Orders', 'Kitchen', 'Tables', 'Cashier']:
            frame = tb.Frame(restaurant_tabs, bootstyle='secondary')
            restaurant_tabs.add(frame, text=tab_name)
            self.tabs[tab_name] = frame

        # Group 2: Accounting
        accounting_frame = tb.Frame(tab_control)
        tab_control.add(accounting_frame, text='Accounting')
        accounting_tabs = tb.Notebook(accounting_frame)
        accounting_tabs.pack(expand=1, fill='both', padx=5, pady=5)
        
        # Accounting tabs
        for tab_name in ['Chart of Accounts', 'Journal Entries', 'General Ledger', 'Reports']:
            frame = tb.Frame(accounting_tabs, bootstyle='secondary')
            accounting_tabs.add(frame, text=tab_name)
            self.tabs[tab_name] = frame

        # Group 3: Financial Management
        financial_frame = tb.Frame(tab_control)
        tab_control.add(financial_frame, text='Financial Management')
        financial_tabs = tb.Notebook(financial_frame)
        financial_tabs.pack(expand=1, fill='both', padx=5, pady=5)
        
        # Financial tabs
        for tab_name in ['Receivables', 'Payables', 'Expenses']:
            frame = tb.Frame(financial_tabs, bootstyle='secondary')
            financial_tabs.add(frame, text=tab_name)
            self.tabs[tab_name] = frame

        # Group 4: Inventory & Purchases
        inventory_frame = tb.Frame(tab_control)
        tab_control.add(inventory_frame, text='Inventory & Purchases')
        inventory_tabs = tb.Notebook(inventory_frame)
        inventory_tabs.pack(expand=1, fill='both', padx=5, pady=5)
        
        # Inventory tabs
        for tab_name in ['Inventory', 'Purchases', 'Suppliers']:
            frame = tb.Frame(inventory_tabs, bootstyle='secondary')
            inventory_tabs.add(frame, text=tab_name)
            self.tabs[tab_name] = frame

        # Group 5: Customers
        customers_frame = tb.Frame(tab_control)
        tab_control.add(customers_frame, text='Customers')
        customers_tabs = tb.Notebook(customers_frame)
        customers_tabs.pack(expand=1, fill='both', padx=5, pady=5)
        
        # Customer tab
        frame = tb.Frame(customers_tabs, bootstyle='secondary')
        customers_tabs.add(frame, text='Customers')
        self.tabs['Customers'] = frame
        
        # Initialize all tabs
        self.init_menu_tab()
        self.init_orders_tab()
        self.init_kitchen_tab()
        self.init_tables_tab()
        self.init_cashier_tab()
        self.init_accounts_tab()
        self.init_journal_tab()
        self.init_ledger_tab()
        self.init_receivables_tab()
        self.init_payables_tab()
        self.init_customers_tab()
        self.init_suppliers_tab()
        self.init_inventory_tab()
        self.init_purchases_tab()
        self.init_expenses_tab()
        self.init_reports_tab()

    def style_treeview(self, tree):
        # Add striped rows for readability
        tree.tag_configure('oddrow', background='#f2f6fa')
        tree.tag_configure('evenrow', background='#e9eef6')

    def insert_treeview_rows(self, tree, rows):
        for i, row in enumerate(rows):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            tree.insert('', 'end', values=row, tags=(tag,))

    def init_accounts_tab(self):
        frame = self.tabs['Chart of Accounts']
        for widget in frame.winfo_children():
            widget.destroy()
        tb.Label(frame, text='Chart of Accounts', style='Section.TLabel').pack(pady=(10, 0))
        entry_frame = tb.Frame(frame)
        entry_frame.pack(pady=10)
        tb.Label(entry_frame, text='Account Name:').grid(row=0, column=0, padx=5, pady=5)
        self.account_name_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.account_name_var, width=25).grid(row=0, column=1, padx=5, pady=5)
        tb.Label(entry_frame, text='Type:').grid(row=0, column=2, padx=5, pady=5)
        self.account_type_var = tb.StringVar()
        tb.Combobox(entry_frame, textvariable=self.account_type_var, values=['Asset', 'Liability', 'Equity', 'Income', 'Expense'], width=20, state='readonly').grid(row=0, column=3, padx=5, pady=5)
        self.account_edit_id = None # Added for editing
        tb.Button(entry_frame, text='Add Account', style='Accent.TButton', command=self.add_account).grid(row=0, column=4, padx=10, pady=5)
        # Search box
        search_frame = tb.Frame(frame)
        search_frame.pack(pady=(0, 5), padx=10, anchor='w')
        tb.Label(search_frame, text='Search:').pack(side='left')
        self.account_search_var = tb.StringVar()
        self.account_search_var.trace('w', lambda *args: self.load_accounts())
        tb.Entry(search_frame, textvariable=self.account_search_var, width=20).pack(side='left', padx=5)
        self.accounts_tree = tb.Treeview(frame, columns=('ID', 'Name', 'Type'), show='headings', height=12, selectmode='browse')
        self.accounts_tree.heading('ID', text='ID')
        self.accounts_tree.heading('Name', text='Name')
        self.accounts_tree.heading('Type', text='Type')
        self.accounts_tree.column('ID', width=40, anchor='center')
        self.accounts_tree.column('Name', width=200)
        self.accounts_tree.column('Type', width=120)
        self.accounts_tree.pack(pady=10, padx=10, fill='x')
        self.style_treeview(self.accounts_tree)
        self.accounts_tree.bind('<<TreeviewSelect>>', self.on_account_select)
        btn_frame = tb.Frame(frame)
        btn_frame.pack(pady=5)
        tb.Button(btn_frame, text='Edit Selected', style='Accent.TButton', command=self.on_edit_account).grid(row=0, column=0, padx=5) # Added edit button
        tb.Button(btn_frame, text='Delete Selected', style='Accent.TButton', command=self.delete_account).grid(row=0, column=1, padx=5)
        self.load_accounts()

    # Added edit functionality for accounts
    def on_account_select(self, event):
        selected = self.accounts_tree.selection()
        if not selected:
            self.account_edit_id = None
            self.account_name_var.set('')
            self.account_type_var.set('')
            return
        item = self.accounts_tree.item(selected[0])['values']
        self.account_edit_id = item[0]
        self.account_name_var.set(item[1])
        self.account_type_var.set(item[2])

    def on_edit_account(self):
        selected = self.accounts_tree.selection()
        if not selected:
            Messagebox.show_warning('Select Account', 'Please select an account to edit.')
            return
        # on_account_select already populates the fields
        self.set_status('Editing account.')

    # Modified add_account to also handle saving edits
    def add_account(self):
        name = self.account_name_var.get().strip()
        acc_type = self.account_type_var.get().strip()
        if not name or not acc_type:
            Messagebox.show_warning('Input Error', 'Please enter both name and type.')
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        if self.account_edit_id:
            c.execute('UPDATE accounts SET name=?, type=? WHERE id=?', (name, acc_type, self.account_edit_id))
            self.set_status('Account updated.')
        else:
            c.execute('INSERT INTO accounts (name, type) VALUES (?, ?)', (name, acc_type))
            self.set_status('Account added.')
        conn.commit()
        conn.close()
        self.account_name_var.set('')
        self.account_type_var.set('')
        self.account_edit_id = None # Reset edit mode
        self.load_accounts()
        self.load_accounts_for_lines() # Refresh account dropdown in Journal Entries

    def load_accounts(self):
        for row in self.accounts_tree.get_children():
            self.accounts_tree.delete(row)
        search = self.account_search_var.get().lower() if hasattr(self, 'account_search_var') else ''
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id, name, type FROM accounts ORDER BY id')
        rows = c.fetchall()
        filtered = [row for row in rows if search in str(row[1]).lower() or search in str(row[2]).lower()]
        self.insert_treeview_rows(self.accounts_tree, filtered)
        conn.close()

    def delete_account(self):
        selected = self.accounts_tree.selection()
        if not selected:
            Messagebox.show_warning('Select Account', 'Please select an account to delete.')
            return
        # Check if account is used in journal entries before deleting
        acc_id = self.accounts_tree.item(selected[0])['values'][0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM journal_lines WHERE account_id=?', (acc_id,))
        count = c.fetchone()[0]
        if count > 0:
            Messagebox.show_warning('Cannot Delete', 'This account is used in journal entries and cannot be deleted.')
            conn.close()
            return
        c.execute('DELETE FROM accounts WHERE id=?', (acc_id,))
        conn.commit()
        conn.close()
        self.load_accounts()
        self.load_accounts_for_lines() # Refresh account dropdown in Journal Entries
        self.set_status('Account deleted.')

    def init_journal_tab(self):
        frame = self.tabs['Journal Entries']
        for widget in frame.winfo_children():
            widget.destroy()
        tb.Label(frame, text='Journal Entries', style='Section.TLabel').pack(pady=(10, 0))
        entry_frame = tb.Frame(frame)
        entry_frame.pack(pady=10)
        tb.Label(entry_frame, text='Date (YYYY-MM-DD):').grid(row=0, column=0, padx=5, pady=5)
        self.journal_date_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.journal_date_var, width=15).grid(row=0, column=1, padx=5, pady=5)
        tb.Label(entry_frame, text='Description:').grid(row=0, column=2, padx=5, pady=5)
        self.journal_desc_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.journal_desc_var, width=30).grid(row=0, column=3, padx=5, pady=5)
        tb.Button(entry_frame, text='Add Entry', style='Accent.TButton', command=self.add_journal_entry).grid(row=0, column=4, padx=10, pady=5)
        tb.Button(entry_frame, text='Refresh', style='Accent.TButton', command=self.load_journal_entries).grid(row=0, column=5, padx=10, pady=5)
        # Journal entries list
        self.journal_tree = tb.Treeview(frame, columns=('ID', 'Date', 'Description'), show='headings', height=8)
        self.journal_tree.heading('ID', text='ID')
        self.journal_tree.heading('Date', text='Date')
        self.journal_tree.heading('Description', text='Description')
        self.journal_tree.column('ID', width=40, anchor='center')
        self.journal_tree.column('Date', width=100)
        self.journal_tree.column('Description', width=250)
        self.journal_tree.pack(pady=10, padx=10, fill='x')
        self.style_treeview(self.journal_tree)
        self.journal_tree.bind('<<TreeviewSelect>>', self.on_journal_select)
        tb.Button(frame, text='Delete Selected Entry', style='Accent.TButton', command=self.delete_journal_entry).pack(pady=5)
        # Journal lines section
        lines_frame = tb.LabelFrame(frame, text='Journal Lines', style='Section.TLabel')
        lines_frame.pack(fill='x', padx=10, pady=10)
        self.journal_lines_tree = tb.Treeview(lines_frame, columns=('ID', 'Account', 'Debit', 'Credit'), show='headings', height=6)
        self.journal_lines_tree.heading('ID', text='ID')
        self.journal_lines_tree.heading('Account', text='Account')
        self.journal_lines_tree.heading('Debit', text='Debit')
        self.journal_lines_tree.heading('Credit', text='Credit')
        self.journal_lines_tree.column('ID', width=40, anchor='center')
        self.journal_lines_tree.column('Account', width=150)
        self.journal_lines_tree.column('Debit', width=100, anchor='e')
        self.journal_lines_tree.column('Credit', width=100, anchor='e')
        self.journal_lines_tree.pack(side='left', padx=5, pady=5)
        # Add line controls
        add_line_frame = tb.Frame(lines_frame)
        add_line_frame.pack(side='left', padx=10)
        tb.Label(add_line_frame, text='Account:').grid(row=0, column=0, padx=2, pady=2)
        self.line_account_var = tb.StringVar()
        self.line_account_cb = tb.Combobox(add_line_frame, textvariable=self.line_account_var, width=18, state='readonly')
        self.line_account_cb.grid(row=0, column=1, padx=2)
        tb.Label(add_line_frame, text='Debit:').grid(row=1, column=0, padx=2, pady=2)
        self.line_debit_var = tb.StringVar()
        tb.Entry(add_line_frame, textvariable=self.line_debit_var, width=10).grid(row=1, column=1, padx=2)
        tb.Label(add_line_frame, text='Credit:').grid(row=2, column=0, padx=2, pady=2)
        self.line_credit_var = tb.StringVar()
        tb.Entry(add_line_frame, textvariable=self.line_credit_var, width=10).grid(row=2, column=2, padx=2) # Moved to column 2
        tb.Button(add_line_frame, text='Add Line', style='Accent.TButton', command=self.add_journal_line).grid(row=3, column=0, columnspan=3, pady=5) # Adjusted columnspan
        tb.Button(add_line_frame, text='Delete Selected Line', style='Accent.TButton', command=self.delete_journal_line).grid(row=4, column=0, columnspan=3, pady=5) # Adjusted columnspan
        self.selected_entry_id = None
        self.load_journal_entries()
        self.load_accounts_for_lines()

    def load_accounts_for_lines(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT name FROM accounts ORDER BY name')
        accounts = [row[0] for row in c.fetchall()]
        self.line_account_cb['values'] = accounts
        conn.close()

    def on_journal_select(self, event):
        selected = self.journal_tree.selection()
        if not selected:
            self.selected_entry_id = None
            self.load_journal_lines(None)
            return
        entry_id = self.journal_tree.item(selected[0])['values'][0]
        self.selected_entry_id = entry_id
        self.load_journal_lines(entry_id)

    def add_journal_line(self):
        if not self.selected_entry_id:
            Messagebox.show_warning('No Entry Selected', 'Select a journal entry first.')
            return
        account_name = self.line_account_var.get().strip()
        debit = self.line_debit_var.get().strip()
        credit = self.line_credit_var.get().strip()
        if not account_name:
            Messagebox.show_warning('Input Error', 'Please select an account.')
            return
        if not debit and not credit:
             Messagebox.show_warning('Input Error', 'Please enter either a debit or a credit amount.')
             return
        if debit and credit:
             Messagebox.show_warning('Input Error', 'Please enter only a debit or a credit amount, not both.')
             return
        try:
            debit_val = float(debit) if debit else 0.0
            credit_val = float(credit) if credit else 0.0
        except ValueError:
            Messagebox.show_warning('Input Error', 'Debit and Credit must be numbers.')
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id FROM accounts WHERE name=?', (account_name,))
        row = c.fetchone()
        if not row:
            Messagebox.show_warning('Account Error', 'Account not found.')
            conn.close()
            return
        account_id = row[0]
        c.execute('INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)',
                  (self.selected_entry_id, account_id, debit_val, credit_val))
        conn.commit()
        conn.close()
        self.line_account_var.set('')
        self.line_debit_var.set('')
        self.line_credit_var.set('')
        self.load_journal_lines(self.selected_entry_id)
        self.load_ledger()
        self.set_status('Journal line added.')

    def load_journal_lines(self, entry_id):
        for row in self.journal_lines_tree.get_children():
            self.journal_lines_tree.delete(row)
        if not entry_id:
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''SELECT jl.id, a.name, jl.debit, jl.credit FROM journal_lines jl
                     JOIN accounts a ON jl.account_id = a.id WHERE jl.entry_id=?''', (entry_id,))
        rows = c.fetchall()
        for row in rows:
            self.journal_lines_tree.insert('', 'end', values=(row[0], row[1], f'{row[2]:.2f}', f'{row[3]:.2f}'))
        conn.close()

    def delete_journal_line(self):
        selected = self.journal_lines_tree.selection()
        if not selected or not self.selected_entry_id:
            Messagebox.show_warning('Select Line', 'Select a journal line to delete.')
            return
        line_id = self.journal_lines_tree.item(selected[0])['values'][0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('DELETE FROM journal_lines WHERE id=?', (line_id,))
        conn.commit()
        conn.close()
        self.load_journal_lines(self.selected_entry_id)
        self.load_ledger()
        self.set_status('Journal line deleted.')

    def add_journal_entry(self):
        date = self.journal_date_var.get().strip()
        desc = self.journal_desc_var.get().strip()
        if not date:
            Messagebox.show_warning('Input Error', 'Please enter a date.')
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('INSERT INTO journal_entries (date, description) VALUES (?, ?)', (date, desc))
        entry_id = c.lastrowid # Get the ID of the newly inserted entry
        conn.commit()
        conn.close()
        self.journal_date_var.set('')
        self.journal_desc_var.set('')
        self.load_journal_entries() # This will auto-select the new entry due to the binding
        self.set_status('Journal entry added.')

    def load_journal_entries(self):
        for row in self.journal_tree.get_children():
            self.journal_tree.delete(row)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id, date, description FROM journal_entries ORDER BY id')
        rows = c.fetchall()
        for row in rows:
            self.journal_tree.insert('', 'end', values=row)
        conn.close()
        # Auto-select the first entry if exists
        entries = self.journal_tree.get_children()
        if entries:
            self.journal_tree.selection_set(entries[0])
            # The binding <<TreeviewSelect>> will call on_journal_select
        else:
            self.selected_entry_id = None
            self.load_journal_lines(None)

    def delete_journal_entry(self):
        selected = self.journal_tree.selection()
        if not selected:
            Messagebox.show_warning('Select Entry', 'Please select a journal entry to delete.')
            return
        entry_id = self.journal_tree.item(selected[0])['values'][0]
        # Optional: Confirm deletion
        # if not Messagebox.yesno('Confirm Delete', 'Are you sure you want to delete this journal entry and all its lines?'):
        #     return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        # Delete related journal lines first
        c.execute('DELETE FROM journal_lines WHERE entry_id=?', (entry_id,))
        c.execute('DELETE FROM journal_entries WHERE id=?', (entry_id,))
        conn.commit()
        conn.close()
        self.load_journal_entries()
        self.load_ledger() # Refresh ledger after deleting entries/lines
        self.set_status('Journal entry deleted.')

    def init_ledger_tab(self):
        frame = self.tabs['General Ledger']
        for widget in frame.winfo_children():
            widget.destroy()
        tb.Label(frame, text='General Ledger', style='Section.TLabel').pack(pady=(10, 0))
        self.ledger_tree = tb.Treeview(frame, columns=('Account', 'Debit', 'Credit', 'Balance'), show='headings', height=18)
        self.ledger_tree.heading('Account', text='Account')
        self.ledger_tree.heading('Debit', text='Debit')
        self.ledger_tree.heading('Credit', text='Credit')
        self.ledger_tree.heading('Balance', text='Balance')
        self.ledger_tree.column('Account', width=200)
        self.ledger_tree.column('Debit', width=100, anchor='e')
        self.ledger_tree.column('Credit', width=100, anchor='e')
        self.ledger_tree.column('Balance', width=100, anchor='e')
        self.ledger_tree.pack(pady=10, padx=10, fill='x')
        tb.Button(frame, text='Refresh Ledger', style='Accent.TButton', command=self.load_ledger).pack(pady=5)
        self.load_ledger()

    def load_ledger(self):
        for row in self.ledger_tree.get_children():
            self.ledger_tree.delete(row)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id, name FROM accounts')
        accounts = c.fetchall()
        for acc_id, acc_name in accounts:
            c.execute('''SELECT SUM(debit), SUM(credit) FROM journal_lines WHERE account_id=?''', (acc_id,))
            debit, credit = c.fetchone()
            debit = debit if debit else 0.0
            credit = credit if credit else 0.0
            balance = debit - credit
            self.ledger_tree.insert('', 'end', values=(acc_name, f'{debit:.2f}', f'{credit:.2f}', f'{balance:.2f}'))
        conn.close()

    def init_receivables_tab(self):
        frame = self.tabs['Receivables']
        for widget in frame.winfo_children():
            widget.destroy()
        tb.Label(frame, text='Accounts Receivable', style='Section.TLabel').pack(pady=(10, 0))
        entry_frame = tb.Frame(frame)
        entry_frame.pack(pady=10)
        tb.Label(entry_frame, text='Customer:').grid(row=0, column=0, padx=5, pady=5)
        self.recv_customer_var = tb.StringVar()
        self.recv_customer_cb = tb.Combobox(entry_frame, textvariable=self.recv_customer_var, width=20, state='readonly')
        self.recv_customer_cb.grid(row=0, column=1, padx=5, pady=5)
        self.load_receivable_customers()
        tb.Label(entry_frame, text='Amount:').grid(row=0, column=2, padx=5, pady=5)
        self.recv_amount_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.recv_amount_var, width=10).grid(row=0, column=3, padx=5, pady=5)
        tb.Label(entry_frame, text='Due Date (YYYY-MM-DD):').grid(row=0, column=4, padx=5, pady=5)
        self.recv_due_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.recv_due_var, width=12).grid(row=0, column=5, padx=5, pady=5)
        tb.Button(entry_frame, text='Add Receivable', style='Accent.TButton', command=self.add_receivable).grid(row=0, column=6, padx=10, pady=5)
        # Search box
        search_frame = tb.Frame(frame)
        search_frame.pack(pady=(0, 5), padx=10, anchor='w')
        tb.Label(search_frame, text='Search:').pack(side='left')
        self.recv_search_var = tb.StringVar()
        self.recv_search_var.trace('w', lambda *args: self.load_receivables())
        tb.Entry(search_frame, textvariable=self.recv_search_var, width=20).pack(side='left', padx=5)
        self.recv_tree = tb.Treeview(frame, columns=('ID', 'Customer', 'Amount', 'Due Date', 'Paid'), show='headings', height=12, selectmode='browse')
        self.recv_tree.heading('ID', text='ID')
        self.recv_tree.heading('Customer', text='Customer')
        self.recv_tree.heading('Amount', text='Amount')
        self.recv_tree.heading('Due Date', text='Due Date')
        self.recv_tree.heading('Paid', text='Paid')
        self.recv_tree.column('ID', width=40, anchor='center')
        self.recv_tree.column('Customer', width=120)
        self.recv_tree.column('Amount', width=80, anchor='e')
        self.recv_tree.column('Due Date', width=100)
        self.recv_tree.column('Paid', width=60, anchor='center')
        self.recv_tree.pack(pady=10, padx=10, fill='x')
        self.style_treeview(self.recv_tree)
        btn_frame = tb.Frame(frame)
        btn_frame.pack(pady=5)
        tb.Button(btn_frame, text='Mark as Paid', style='Accent.TButton', command=self.mark_receivable_paid).grid(row=0, column=0, padx=5)
        tb.Button(btn_frame, text='Mark as Unpaid', style='Accent.TButton', command=self.mark_receivable_unpaid).grid(row=0, column=1, padx=5)
        tb.Button(btn_frame, text='Delete Selected', style='Accent.TButton', command=self.delete_receivable).grid(row=0, column=2, padx=5)
        self.load_receivables()

    def load_receivable_customers(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT name FROM customers ORDER BY name')
        customers = [row[0] for row in c.fetchall()]
        self.recv_customer_cb['values'] = customers
        conn.close()

    def add_receivable(self):
        customer = self.recv_customer_var.get().strip()
        amount = self.recv_amount_var.get().strip()
        due = self.recv_due_var.get().strip()
        if not customer or not amount or not due:
            self.set_status('Please fill all fields.', error=True)
            return
        try:
            amount_val = float(amount)
        except ValueError:
            self.set_status('Amount must be a number.', error=True)
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id FROM customers WHERE name=?', (customer,))
        row = c.fetchone()
        customer_id = row[0] if row else None
        c.execute('INSERT INTO receivables (customer, amount, due_date, paid) VALUES (?, ?, ?, 0)', (customer, amount_val, due))
        # Journal entry: Debit AR, Credit Sales Revenue
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        c.execute('INSERT INTO journal_entries (date, description) VALUES (?, ?)', (today, f"Receivable from {customer}"))
        entry_id = c.lastrowid
        # Get account IDs
        c.execute('SELECT id FROM accounts WHERE name = "Accounts Receivable"')
        ar_id = c.fetchone()[0]
        c.execute('SELECT id FROM accounts WHERE name = "Sales Revenue"')
        sales_id = c.fetchone()[0]
        c.execute('INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)', (entry_id, ar_id, amount_val, 0))
        c.execute('INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)', (entry_id, sales_id, 0, amount_val))
        conn.commit()
        conn.close()
        self.recv_customer_var.set('')
        self.recv_amount_var.set('')
        self.recv_due_var.set('')
        self.load_receivables()
        self.set_status('Receivable added.')

    def load_receivables(self):
        for row in self.recv_tree.get_children():
            self.recv_tree.delete(row)
        search = self.recv_search_var.get().lower() if hasattr(self, 'recv_search_var') else ''
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id, customer, amount, due_date, paid FROM receivables ORDER BY id')
        rows = c.fetchall()
        filtered = [row for row in rows if search in str(row[1]).lower() or search in str(row[3]).lower()]
        for i, row in enumerate(filtered):
            paid_str = 'Yes' if row[4] else 'No'
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.recv_tree.insert('', 'end', values=(row[0], row[1], f'{row[2]:.2f}', row[3], paid_str), tags=(tag,))
        conn.close()

    def set_status(self, message, error=False):
        if not hasattr(self, 'status_var'):
            self.status_var = tb.StringVar()
            status_bar = tb.Label(self, textvariable=self.status_var, anchor='w', relief='sunken', font=('Segoe UI', 10))
            status_bar.pack(side='bottom', fill='x')
        self.status_var.set(message)
        if error:
            self.after(4000, lambda: self.status_var.set(''))

    def mark_receivable_paid(self):
        selected = self.recv_tree.selection()
        if not selected:
            Messagebox.show_warning('Select Receivable', 'Select a receivable to mark as paid.')
            return
        recv_id = self.recv_tree.item(selected[0])['values'][0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('UPDATE receivables SET paid=1 WHERE id=?', (recv_id,))
        conn.commit()
        conn.close()
        self.load_receivables()

    def mark_receivable_unpaid(self):
        selected = self.recv_tree.selection()
        if not selected:
            messagebox.showwarning('Select Receivable', 'Select a receivable to mark as unpaid.')
            return
        recv_id = self.recv_tree.item(selected[0])['values'][0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('UPDATE receivables SET paid=0 WHERE id=?', (recv_id,))
        conn.commit()
        conn.close()
        self.load_receivables()

    def delete_receivable(self):
        selected = self.recv_tree.selection()
        if not selected:
            messagebox.showwarning('Select Receivable', 'Select a receivable to delete.')
            return
        recv_id = self.recv_tree.item(selected[0])['values'][0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('DELETE FROM receivables WHERE id=?', (recv_id,))
        conn.commit()
        conn.close()
        self.load_receivables()

    def init_payables_tab(self):
        frame = self.tabs['Payables']
        for widget in frame.winfo_children():
            widget.destroy()
        tb.Label(frame, text='Accounts Payable', style='Section.TLabel').pack(pady=(10, 0))
        entry_frame = tb.Frame(frame)
        entry_frame.pack(pady=10)
        tb.Label(entry_frame, text='Supplier:').grid(row=0, column=0, padx=5, pady=5)
        self.pay_supplier_var = tb.StringVar()
        self.pay_supplier_cb = tb.Combobox(entry_frame, textvariable=self.pay_supplier_var, width=20, state='readonly')
        self.pay_supplier_cb.grid(row=0, column=1, padx=5, pady=5)
        self.load_payable_suppliers()
        tb.Label(entry_frame, text='Amount:').grid(row=0, column=2, padx=5, pady=5)
        self.pay_amount_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.pay_amount_var, width=10).grid(row=0, column=3, padx=5, pady=5)
        tb.Label(entry_frame, text='Due Date (YYYY-MM-DD):').grid(row=0, column=4, padx=5, pady=5)
        self.pay_due_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.pay_due_var, width=12).grid(row=0, column=5, padx=5, pady=5)
        tb.Button(entry_frame, text='Add Payable', style='Accent.TButton', command=self.add_payable).grid(row=0, column=6, padx=10, pady=5)
        # Search box
        search_frame = tb.Frame(frame)
        search_frame.pack(pady=(0, 5), padx=10, anchor='w')
        tb.Label(search_frame, text='Search:').pack(side='left')
        self.pay_search_var = tb.StringVar()
        self.pay_search_var.trace('w', lambda *args: self.load_payables())
        tb.Entry(search_frame, textvariable=self.pay_search_var, width=20).pack(side='left', padx=5)
        self.pay_tree = tb.Treeview(frame, columns=('ID', 'Supplier', 'Amount', 'Due Date', 'Paid'), show='headings', height=12, selectmode='browse')
        self.pay_tree.heading('ID', text='ID')
        self.pay_tree.heading('Supplier', text='Supplier')
        self.pay_tree.heading('Amount', text='Amount')
        self.pay_tree.heading('Due Date', text='Due Date')
        self.pay_tree.heading('Paid', text='Paid')
        self.pay_tree.column('ID', width=40, anchor='center')
        self.pay_tree.column('Supplier', width=120)
        self.pay_tree.column('Amount', width=80, anchor='e')
        self.pay_tree.column('Due Date', width=100)
        self.pay_tree.column('Paid', width=60, anchor='center')
        self.pay_tree.pack(pady=10, padx=10, fill='x')
        self.style_treeview(self.pay_tree)
        btn_frame = tb.Frame(frame)
        btn_frame.pack(pady=5)
        tb.Button(btn_frame, text='Mark as Paid', style='Accent.TButton', command=self.mark_payable_paid).grid(row=0, column=0, padx=5)
        tb.Button(btn_frame, text='Mark as Unpaid', style='Accent.TButton', command=self.mark_payable_unpaid).grid(row=0, column=1, padx=5)
        tb.Button(btn_frame, text='Delete Selected', style='Accent.TButton', command=self.delete_payable).grid(row=0, column=2, padx=5)
        self.load_payables()

    def load_payable_suppliers(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT name FROM suppliers ORDER BY name')
        suppliers = [row[0] for row in c.fetchall()]
        self.pay_supplier_cb['values'] = suppliers
        conn.close()

    def add_payable(self):
        supplier = self.pay_supplier_var.get().strip()
        amount = self.pay_amount_var.get().strip()
        due = self.pay_due_var.get().strip()
        if not supplier or not amount or not due:
            self.set_status('Please fill all fields.', error=True)
            return
        try:
            amount_val = float(amount)
        except ValueError:
            self.set_status('Amount must be a number.', error=True)
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id FROM suppliers WHERE name=?', (supplier,))
        row = c.fetchone()
        supplier_id = row[0] if row else None
        c.execute('INSERT INTO payables (vendor, amount, due_date, paid) VALUES (?, ?, ?, 0)', (supplier, amount_val, due))
        # Journal entry: Debit Expense, Credit Accounts Payable
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        c.execute('INSERT INTO journal_entries (date, description) VALUES (?, ?)', (today, f"Payable to {supplier}"))
        entry_id = c.lastrowid
        # Get account IDs
        c.execute('SELECT id FROM accounts WHERE name = "Operating Expenses"')
        exp_id = c.fetchone()[0]
        c.execute('SELECT id FROM accounts WHERE name = "Accounts Payable"')
        ap_id = c.fetchone()[0]
        c.execute('INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)', (entry_id, exp_id, amount_val, 0))
        c.execute('INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)', (entry_id, ap_id, 0, amount_val))
        conn.commit()
        conn.close()
        self.pay_supplier_var.set('')
        self.pay_amount_var.set('')
        self.pay_due_var.set('')
        self.load_payables()
        self.set_status('Payable added.')

    def load_payables(self):
        for row in self.pay_tree.get_children():
            self.pay_tree.delete(row)
        search = self.pay_search_var.get().lower() if hasattr(self, 'pay_search_var') else ''
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id, vendor, amount, due_date, paid FROM payables ORDER BY id')
        rows = c.fetchall()
        filtered = [row for row in rows if search in str(row[1]).lower() or search in str(row[3]).lower()]
        for i, row in enumerate(filtered):
            paid_str = 'Yes' if row[4] else 'No'
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.pay_tree.insert('', 'end', values=(row[0], row[1], f'{row[2]:.2f}', row[3], paid_str), tags=(tag,))
        conn.close()

    def mark_payable_paid(self):
        selected = self.pay_tree.selection()
        if not selected:
            messagebox.showwarning('Select Payable', 'Select a payable to mark as paid.')
            return
        pay_id = self.pay_tree.item(selected[0])['values'][0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('UPDATE payables SET paid=1 WHERE id=?', (pay_id,))
        conn.commit()
        conn.close()
        self.load_payables()

    def mark_payable_unpaid(self):
        selected = self.pay_tree.selection()
        if not selected:
            messagebox.showwarning('Select Payable', 'Select a payable to mark as unpaid.')
            return
        pay_id = self.pay_tree.item(selected[0])['values'][0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('UPDATE payables SET paid=0 WHERE id=?', (pay_id,))
        conn.commit()
        conn.close()
        self.load_payables()

    def delete_payable(self):
        selected = self.pay_tree.selection()
        if not selected:
            messagebox.showwarning('Select Payable', 'Select a payable to delete.')
            return
        pay_id = self.pay_tree.item(selected[0])['values'][0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('DELETE FROM payables WHERE id=?', (pay_id,))
        conn.commit()
        conn.close()
        self.load_payables()

    def init_customers_tab(self):
        frame = self.tabs['Customers']
        for widget in frame.winfo_children():
            widget.destroy()
        tb.Label(frame, text='Customers', style='Section.TLabel').pack(pady=(10, 0))
        entry_frame = tb.Frame(frame)
        entry_frame.pack(pady=10)
        tb.Label(entry_frame, text='Name:').grid(row=0, column=0, padx=5, pady=5)
        self.customer_name_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.customer_name_var, width=25).grid(row=0, column=1, padx=5, pady=5)
        tb.Label(entry_frame, text='Contact:').grid(row=0, column=2, padx=5, pady=5)
        self.customer_contact_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.customer_contact_var, width=25).grid(row=0, column=3, padx=5, pady=5)
        self.customer_edit_id = None
        tb.Button(entry_frame, text='Add/Save Customer', style='Accent.TButton', command=self.save_customer).grid(row=0, column=4, padx=10, pady=5)
        # Search box
        search_frame = tb.Frame(frame)
        search_frame.pack(pady=(0, 5), padx=10, anchor='w')
        tb.Label(search_frame, text='Search:').pack(side='left')
        self.customer_search_var = tb.StringVar()
        self.customer_search_var.trace('w', lambda *args: self.load_customers())
        tb.Entry(search_frame, textvariable=self.customer_search_var, width=20).pack(side='left', padx=5)
        self.customers_tree = tb.Treeview(frame, columns=('ID', 'Name', 'Contact'), show='headings', height=12, selectmode='browse')
        self.customers_tree.heading('ID', text='ID')
        self.customers_tree.heading('Name', text='Name')
        self.customers_tree.heading('Contact', text='Contact')
        self.customers_tree.column('ID', width=40, anchor='center')
        self.customers_tree.column('Name', width=200)
        self.customers_tree.column('Contact', width=200)
        self.customers_tree.pack(pady=10, padx=10, fill='x')
        self.style_treeview(self.customers_tree)
        self.customers_tree.bind('<<TreeviewSelect>>', self.on_customer_select)
        btn_frame = tb.Frame(frame)
        btn_frame.pack(pady=5)
        tb.Button(btn_frame, text='Delete Selected', style='Accent.TButton', command=self.delete_customer).grid(row=0, column=0, padx=5)
        self.load_customers()

    def save_customer(self):
        name = self.customer_name_var.get().strip()
        contact = self.customer_contact_var.get().strip()
        if not name:
            self.set_status('Please enter a name.', error=True)
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        if self.customer_edit_id:
            c.execute('UPDATE customers SET name=?, contact=? WHERE id=?', (name, contact, self.customer_edit_id))
            self.set_status('Customer updated.')
        else:
            c.execute('INSERT INTO customers (name, contact) VALUES (?, ?)', (name, contact))
            self.set_status('Customer added.')
        conn.commit()
        conn.close()
        self.customer_name_var.set('')
        self.customer_contact_var.set('')
        self.customer_edit_id = None
        self.load_customers()
        self.load_receivable_customers()

    def on_customer_select(self, event):
        selected = self.customers_tree.selection()
        if not selected:
            self.customer_edit_id = None
            self.customer_name_var.set('')
            self.customer_contact_var.set('')
            return
        item = self.customers_tree.item(selected[0])['values']
        self.customer_edit_id = item[0]
        self.customer_name_var.set(item[1])
        self.customer_contact_var.set(item[2])

    def load_customers(self):
        for row in self.customers_tree.get_children():
            self.customers_tree.delete(row)
        search = self.customer_search_var.get().lower() if hasattr(self, 'customer_search_var') else ''
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id, name, contact FROM customers ORDER BY id')
        rows = c.fetchall()
        filtered = [row for row in rows if search in str(row[1]).lower() or search in str(row[2]).lower()]
        self.insert_treeview_rows(self.customers_tree, filtered)
        conn.close()

    def delete_customer(self):
        selected = self.customers_tree.selection()
        if not selected:
            messagebox.showwarning('Select Customer', 'Select a customer to delete.')
            return
        cust_id = self.customers_tree.item(selected[0])['values'][0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('DELETE FROM customers WHERE id=?', (cust_id,))
        conn.commit()
        conn.close()
        self.load_customers()

    def init_suppliers_tab(self):
        frame = self.tabs['Suppliers']
        for widget in frame.winfo_children():
            widget.destroy()
        tb.Label(frame, text='Suppliers', style='Section.TLabel').pack(pady=(10, 0))
        entry_frame = tb.Frame(frame)
        entry_frame.pack(pady=10)
        tb.Label(entry_frame, text='Name:').grid(row=0, column=0, padx=5, pady=5)
        self.supplier_name_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.supplier_name_var, width=25).grid(row=0, column=1, padx=5, pady=5)
        tb.Label(entry_frame, text='Contact:').grid(row=0, column=2, padx=5, pady=5)
        self.supplier_contact_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.supplier_contact_var, width=25).grid(row=0, column=3, padx=5, pady=5)
        self.supplier_edit_id = None
        tb.Button(entry_frame, text='Add/Save Supplier', style='Accent.TButton', command=self.save_supplier).grid(row=0, column=4, padx=10, pady=5)
        # Search box
        search_frame = tb.Frame(frame)
        search_frame.pack(pady=(0, 5), padx=10, anchor='w')
        tb.Label(search_frame, text='Search:').pack(side='left')
        self.supplier_search_var = tb.StringVar()
        self.supplier_search_var.trace('w', lambda *args: self.load_suppliers())
        tb.Entry(search_frame, textvariable=self.supplier_search_var, width=20).pack(side='left', padx=5)
        self.suppliers_tree = tb.Treeview(frame, columns=('ID', 'Name', 'Contact'), show='headings', height=12, selectmode='browse')
        self.suppliers_tree.heading('ID', text='ID')
        self.suppliers_tree.heading('Name', text='Name')
        self.suppliers_tree.heading('Contact', text='Contact')
        self.suppliers_tree.column('ID', width=40, anchor='center')
        self.suppliers_tree.column('Name', width=200)
        self.suppliers_tree.column('Contact', width=200)
        self.suppliers_tree.pack(pady=10, padx=10, fill='x')
        self.style_treeview(self.suppliers_tree)
        self.suppliers_tree.bind('<<TreeviewSelect>>', self.on_supplier_select)
        btn_frame = tb.Frame(frame)
        btn_frame.pack(pady=5)
        tb.Button(btn_frame, text='Delete Selected', style='Accent.TButton', command=self.delete_supplier).grid(row=0, column=0, padx=5)
        self.load_suppliers()

    def save_supplier(self):
        name = self.supplier_name_var.get().strip()
        contact = self.supplier_contact_var.get().strip()
        if not name:
            self.set_status('Please enter a name.', error=True)
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        if self.supplier_edit_id:
            c.execute('UPDATE suppliers SET name=?, contact=? WHERE id=?', (name, contact, self.supplier_edit_id))
            self.set_status('Supplier updated.')
        else:
            c.execute('INSERT INTO suppliers (name, contact) VALUES (?, ?)', (name, contact))
            self.set_status('Supplier added.')
        conn.commit()
        conn.close()
        self.supplier_name_var.set('')
        self.supplier_contact_var.set('')
        self.supplier_edit_id = None
        self.load_suppliers()
        self.load_payable_suppliers()
        self.load_purchase_suppliers()  # Refresh supplier dropdown in Purchases tab

    def on_supplier_select(self, event):
        selected = self.suppliers_tree.selection()
        if not selected:
            self.supplier_edit_id = None
            self.supplier_name_var.set('')
            self.supplier_contact_var.set('')
            return
        item = self.suppliers_tree.item(selected[0])['values']
        self.supplier_edit_id = item[0]
        self.supplier_name_var.set(item[1])
        self.supplier_contact_var.set(item[2])

    def delete_supplier(self):
        selected = self.suppliers_tree.selection()
        if not selected:
            messagebox.showwarning('Select Supplier', 'Select a supplier to delete.')
            return
        supp_id = self.suppliers_tree.item(selected[0])['values'][0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('DELETE FROM suppliers WHERE id=?', (supp_id,))
        conn.commit()
        conn.close()
        self.load_suppliers()

    def init_inventory_tab(self):
        frame = self.tabs['Inventory']
        for widget in frame.winfo_children():
            widget.destroy()
        # Header with title and refresh button
        header_frame = tb.Frame(frame)
        header_frame.pack(fill='x', padx=10, pady=5)
        tb.Label(header_frame, text='Inventory Management', style='Section.TLabel').pack(side='left')
        tb.Button(header_frame, text='Refresh', style='Accent.TButton', command=self.load_inventory).pack(side='right')
        # Entry form in a single labeled frame, using grid
        entry_frame = tb.LabelFrame(frame, text='Add/Edit Inventory Item', style='Section.TLabel')
        entry_frame.pack(fill='x', padx=10, pady=5)
        tb.Label(entry_frame, text='Name:').grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.inv_name_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.inv_name_var, width=20).grid(row=0, column=1, padx=5, pady=5)
        tb.Label(entry_frame, text='SKU:').grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.inv_sku_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.inv_sku_var, width=15).grid(row=0, column=3, padx=5, pady=5)
        tb.Label(entry_frame, text='Quantity:').grid(row=0, column=4, padx=5, pady=5, sticky='e')
        self.inv_qty_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.inv_qty_var, width=8).grid(row=0, column=5, padx=5, pady=5)
        tb.Label(entry_frame, text='Cost:').grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.inv_cost_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.inv_cost_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        tb.Label(entry_frame, text='Price:').grid(row=1, column=2, padx=5, pady=5, sticky='e')
        self.inv_price_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.inv_price_var, width=10).grid(row=1, column=3, padx=5, pady=5)
        self.inv_edit_id = None
        tb.Button(entry_frame, text='Add/Save Item', style='Accent.TButton', command=self.save_inventory_item).grid(row=1, column=4, columnspan=2, padx=10, pady=5, sticky='w')
        # Search box
        search_frame = tb.Frame(frame)
        search_frame.pack(fill='x', padx=10, pady=5)
        tb.Label(search_frame, text='Search:').pack(side='left')
        self.inv_search_var = tb.StringVar()
        self.inv_search_var.trace('w', lambda *args: self.load_inventory())
        tb.Entry(search_frame, textvariable=self.inv_search_var, width=20).pack(side='left', padx=5)
        # Inventory list
        list_frame = tb.LabelFrame(frame, text='Inventory Items', style='Section.TLabel')
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        self.inventory_tree = tb.Treeview(list_frame, 
            columns=('ID', 'Name', 'SKU', 'Quantity', 'Cost', 'Price', 'Value'),
            show='headings', height=12, selectmode='browse')
        self.inventory_tree.heading('ID', text='ID')
        self.inventory_tree.heading('Name', text='Name')
        self.inventory_tree.heading('SKU', text='SKU')
        self.inventory_tree.heading('Quantity', text='Quantity')
        self.inventory_tree.heading('Cost', text='Cost')
        self.inventory_tree.heading('Price', text='Price')
        self.inventory_tree.heading('Value', text='Total Value')
        self.inventory_tree.column('ID', width=40, anchor='center')
        self.inventory_tree.column('Name', width=120)
        self.inventory_tree.column('SKU', width=80)
        self.inventory_tree.column('Quantity', width=80, anchor='e')
        self.inventory_tree.column('Cost', width=80, anchor='e')
        self.inventory_tree.column('Price', width=80, anchor='e')
        self.inventory_tree.column('Value', width=100, anchor='e')
        self.inventory_tree.pack(fill='both', expand=True, padx=5, pady=5)
        self.style_treeview(self.inventory_tree)
        self.inventory_tree.bind('<<TreeviewSelect>>', self.on_inventory_select)
        # Buttons frame
        btn_frame = tb.Frame(frame)
        btn_frame.pack(pady=5)
        tb.Button(btn_frame, text='Delete Selected', style='Accent.TButton', command=self.delete_inventory_item).pack(side='left', padx=5)
        self.load_inventory()

    def load_inventory(self):
        for row in self.inventory_tree.get_children():
            self.inventory_tree.delete(row)
        search = self.inv_search_var.get().lower() if hasattr(self, 'inv_search_var') else ''
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id, name, sku, quantity, cost, price FROM inventory ORDER BY name')
        rows = c.fetchall()
        filtered = [row for row in rows if search in str(row[1]).lower() or search in str(row[2]).lower()]
        
        # Calculate total value for each item
        formatted_rows = []
        for row in filtered:
            total_value = row[3] * row[4]  # quantity * cost
            formatted_row = list(row)
            formatted_row.append(f'{total_value:.2f}')
            formatted_rows.append(formatted_row)
        
        self.insert_treeview_rows(self.inventory_tree, formatted_rows)
        conn.close()

    def init_purchases_tab(self):
        frame = self.tabs['Purchases']
        for widget in frame.winfo_children():
            widget.destroy()
        tb.Label(frame, text='Purchases', style='Section.TLabel').pack(pady=(10, 0))
        entry_frame = tb.Frame(frame)
        entry_frame.pack(pady=10)
        tb.Label(entry_frame, text='Date (YYYY-MM-DD):').grid(row=0, column=0, padx=5, pady=5)
        self.purchase_date_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.purchase_date_var, width=15).grid(row=0, column=1, padx=5, pady=5)
        tb.Label(entry_frame, text='Supplier:').grid(row=0, column=2, padx=5, pady=5)
        self.purchase_supplier_var = tb.StringVar()
        self.purchase_supplier_cb = tb.Combobox(entry_frame, textvariable=self.purchase_supplier_var, width=20, state='readonly')
        self.purchase_supplier_cb.grid(row=0, column=3, padx=5, pady=5)
        self.load_purchase_suppliers()  # Ensure dropdown is populated on tab init
        tb.Button(entry_frame, text='Add Purchase', style='Accent.TButton', command=self.add_purchase).grid(row=0, column=4, padx=10, pady=5)
        self.purchases_tree = tb.Treeview(frame, columns=('ID', 'Date', 'Supplier', 'Total'), show='headings', height=8)
        self.purchases_tree.heading('ID', text='ID')
        self.purchases_tree.heading('Date', text='Date')
        self.purchases_tree.heading('Supplier', text='Supplier')
        self.purchases_tree.heading('Total', text='Total')
        self.purchases_tree.column('ID', width=40, anchor='center')
        self.purchases_tree.column('Date', width=100)
        self.purchases_tree.column('Supplier', width=150)
        self.purchases_tree.column('Total', width=100, anchor='e')
        self.purchases_tree.pack(pady=10, padx=10, fill='x')
        self.style_treeview(self.purchases_tree)
        self.purchases_tree.bind('<<TreeviewSelect>>', self.on_purchase_select)
        tb.Button(frame, text='Delete Selected', style='Accent.TButton', command=self.delete_purchase).pack(pady=5)
        # Purchase items section
        items_frame = tb.LabelFrame(frame, text='Purchase Items', style='Section.TLabel')
        items_frame.pack(fill='x', padx=10, pady=10)
        self.purchase_items_tree = tb.Treeview(items_frame, columns=('ID', 'Item', 'Quantity', 'Cost'), show='headings', height=6)
        self.purchase_items_tree.heading('ID', text='ID')
        self.purchase_items_tree.heading('Item', text='Item')
        self.purchase_items_tree.heading('Quantity', text='Quantity')
        self.purchase_items_tree.heading('Cost', text='Cost')
        self.purchase_items_tree.column('ID', width=40, anchor='center')
        self.purchase_items_tree.column('Item', width=150)
        self.purchase_items_tree.column('Quantity', width=80, anchor='e')
        self.purchase_items_tree.column('Cost', width=100, anchor='e')
        self.purchase_items_tree.pack(side='left', padx=5, pady=5)
        self.style_treeview(self.purchase_items_tree)
        add_item_frame = tb.Frame(items_frame)
        add_item_frame.pack(side='left', padx=10)
        tb.Label(add_item_frame, text='Item:').grid(row=0, column=0, padx=2, pady=2)
        self.purchase_item_var = tb.StringVar()
        self.purchase_item_cb = tb.Combobox(add_item_frame, textvariable=self.purchase_item_var, width=18, state='readonly')
        self.purchase_item_cb.grid(row=0, column=1, padx=2)
        tb.Label(add_item_frame, text='Quantity:').grid(row=1, column=0, padx=2, pady=2)
        self.purchase_qty_var = tb.StringVar()
        tb.Entry(add_item_frame, textvariable=self.purchase_qty_var, width=10).grid(row=1, column=1, padx=2)
        tb.Label(add_item_frame, text='Cost:').grid(row=2, column=0, padx=2, pady=2)
        self.purchase_cost_var = tb.StringVar()
        tb.Entry(add_item_frame, textvariable=self.purchase_cost_var, width=10).grid(row=2, column=1, padx=2)
        tb.Button(add_item_frame, text='Add Item', style='Accent.TButton', command=self.add_purchase_item).grid(row=3, column=0, columnspan=2, pady=5)
        tb.Button(add_item_frame, text='Delete Selected Item', style='Accent.TButton', command=self.delete_purchase_item).grid(row=4, column=0, columnspan=2, pady=5)
        self.selected_purchase_id = None
        self.load_purchase_items_inventory()
        self.load_purchases()

    def load_purchase_suppliers(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT name FROM suppliers ORDER BY name')
        suppliers = [row[0] for row in c.fetchall()]
        self.purchase_supplier_cb['values'] = suppliers
        conn.close()

    def add_purchase(self):
        date = self.purchase_date_var.get().strip()
        supplier_name = self.purchase_supplier_var.get().strip()
        if not date or not supplier_name:
            self.set_status('Please enter date and supplier.', error=True)
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id FROM suppliers WHERE name=?', (supplier_name,))
        row = c.fetchone()
        if not row:
            self.set_status('Supplier not found.', error=True)
            conn.close()
            return
        supplier_id = row[0]
        c.execute('INSERT INTO purchases (date, supplier_id, total) VALUES (?, ?, 0)', (date, supplier_id))
        conn.commit()
        conn.close()
        self.purchase_date_var.set('')
        self.purchase_supplier_var.set('')
        self.load_purchases()
        self.set_status('Purchase added.')

    def load_purchase_items_inventory(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT name FROM inventory ORDER BY name')
        items = [row[0] for row in c.fetchall()]
        self.purchase_item_cb['values'] = items
        conn.close()

    def on_purchase_select(self, event):
        selected = self.purchases_tree.selection()
        if not selected:
            self.selected_purchase_id = None
            self.load_purchase_items(None)
            return
        purchase_id = self.purchases_tree.item(selected[0])['values'][0]
        self.selected_purchase_id = purchase_id
        self.load_purchase_items(purchase_id)

    def add_purchase_item(self):
        if not self.selected_purchase_id:
            Messagebox.show_warning('No Purchase Selected', 'Select a purchase first.')
            return
        item_name = self.purchase_item_var.get()
        qty = self.purchase_qty_var.get().strip()
        cost = self.purchase_cost_var.get().strip()
        if not item_name or not qty or not cost:
            Messagebox.show_warning('Input Error', 'Enter item, quantity, and cost.')
            return
        try:
            qty_val = int(qty)
            cost_val = float(cost)
        except ValueError:
            Messagebox.show_warning('Input Error', 'Quantity and Cost must be numbers.')
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id FROM inventory WHERE name=?', (item_name,))
        row = c.fetchone()
        if not row:
            Messagebox.show_warning('Item Error', 'Inventory item not found.')
            conn.close()
            return
        item_id = row[0]
        # Add purchase item
        c.execute('INSERT INTO purchase_items (purchase_id, inventory_id, quantity, cost) VALUES (?, ?, ?, ?)',
                  (self.selected_purchase_id, item_id, qty_val, cost_val))
        # Update inventory quantity
        c.execute('UPDATE inventory SET quantity = quantity + ? WHERE id=?', (qty_val, item_id))
        # Update purchase total
        c.execute('SELECT SUM(quantity * cost) FROM purchase_items WHERE purchase_id=?', (self.selected_purchase_id,))
        total = c.fetchone()[0] or 0.0
        c.execute('UPDATE purchases SET total=? WHERE id=?', (total, self.selected_purchase_id))
        conn.commit()
        conn.close()
        self.purchase_item_var.set('')
        self.purchase_qty_var.set('')
        self.purchase_cost_var.set('')
        self.load_purchase_items(self.selected_purchase_id)
        self.load_inventory()
        self.load_purchases()

    def load_purchase_items(self, purchase_id):
        for row in self.purchase_items_tree.get_children():
            self.purchase_items_tree.delete(row)
        if not purchase_id:
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''SELECT pi.id, i.name, pi.quantity, pi.cost FROM purchase_items pi
                     JOIN inventory i ON pi.inventory_id = i.id WHERE pi.purchase_id=?''', (purchase_id,))
        rows = c.fetchall()
        self.insert_treeview_rows(self.purchase_items_tree, rows)
        conn.close()

    def delete_purchase_item(self):
        selected = self.purchase_items_tree.selection()
        if not selected or not self.selected_purchase_id:
            messagebox.showwarning('Select Item', 'Select a purchase item to delete.')
            return
        item_id = self.purchase_items_tree.item(selected[0])['values'][0]
        # Get quantity and inventory_id to update inventory
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT inventory_id, quantity FROM purchase_items WHERE id=?', (item_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return
        inventory_id, qty = row
        # Delete purchase item
        c.execute('DELETE FROM purchase_items WHERE id=?', (item_id,))
        # Update inventory quantity
        c.execute('UPDATE inventory SET quantity = quantity - ? WHERE id=?', (qty, inventory_id))
        # Update purchase total
        c.execute('SELECT SUM(quantity * cost) FROM purchase_items WHERE purchase_id=?', (self.selected_purchase_id,))
        total = c.fetchone()[0] or 0.0
        c.execute('UPDATE purchases SET total=? WHERE id=?', (total, self.selected_purchase_id))
        conn.commit()
        conn.close()
        self.load_purchase_items(self.selected_purchase_id)
        self.load_inventory()
        self.load_purchases()

    def load_purchases(self):
        for row in self.purchases_tree.get_children():
            self.purchases_tree.delete(row)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''SELECT p.id, p.date, s.name, p.total FROM purchases p LEFT JOIN suppliers s ON p.supplier_id = s.id ORDER BY p.id''')
        rows = c.fetchall()
        self.insert_treeview_rows(self.purchases_tree, rows)
        conn.close()

    def delete_purchase(self):
        selected = self.purchases_tree.selection()
        if not selected:
            messagebox.showwarning('Select Purchase', 'Select a purchase to delete.')
            return
        purchase_id = self.purchases_tree.item(selected[0])['values'][0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('DELETE FROM purchases WHERE id=?', (purchase_id,))
        conn.commit()
        conn.close()
        self.load_purchases()

    def init_expenses_tab(self):
        frame = self.tabs['Expenses']
        for widget in frame.winfo_children():
            widget.destroy()
        tb.Label(frame, text='Expenses', style='Section.TLabel').pack(pady=(10, 0))
        entry_frame = tb.Frame(frame)
        entry_frame.pack(pady=10)
        tb.Label(entry_frame, text='Date (YYYY-MM-DD):').grid(row=0, column=0, padx=5, pady=5)
        self.expense_date_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.expense_date_var, width=15).grid(row=0, column=1, padx=5, pady=5)
        tb.Label(entry_frame, text='Type:').grid(row=0, column=2, padx=5, pady=5)
        self.expense_type_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.expense_type_var, width=20).grid(row=0, column=3, padx=5, pady=5)
        tb.Label(entry_frame, text='Amount:').grid(row=0, column=4, padx=5, pady=5)
        self.expense_amount_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.expense_amount_var, width=10).grid(row=0, column=5, padx=5, pady=5)
        tb.Label(entry_frame, text='Description:').grid(row=0, column=6, padx=5, pady=5)
        self.expense_desc_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.expense_desc_var, width=25).grid(row=0, column=7, padx=5, pady=5)
        self.expense_edit_id = None
        tb.Button(entry_frame, text='Add/Save Expense', style='Accent.TButton', command=self.save_expense).grid(row=0, column=8, padx=10, pady=5)
        # Search box
        search_frame = tb.Frame(frame)
        search_frame.pack(pady=(0, 5), padx=10, anchor='w')
        tb.Label(search_frame, text='Search:').pack(side='left')
        self.expense_search_var = tb.StringVar()
        self.expense_search_var.trace('w', lambda *args: self.load_expenses())
        tb.Entry(search_frame, textvariable=self.expense_search_var, width=20).pack(side='left', padx=5)
        self.expenses_tree = tb.Treeview(frame, columns=('ID', 'Date', 'Type', 'Amount', 'Description'), show='headings', height=12, selectmode='browse')
        self.expenses_tree.heading('ID', text='ID')
        self.expenses_tree.heading('Date', text='Date')
        self.expenses_tree.heading('Type', text='Type')
        self.expenses_tree.heading('Amount', text='Amount')
        self.expenses_tree.heading('Description', text='Description')
        self.expenses_tree.column('ID', width=40, anchor='center')
        self.expenses_tree.column('Date', width=100)
        self.expenses_tree.column('Type', width=120)
        self.expenses_tree.column('Amount', width=100, anchor='e')
        self.expenses_tree.column('Description', width=200)
        self.expenses_tree.pack(pady=10, padx=10, fill='x')
        self.style_treeview(self.expenses_tree)
        self.expenses_tree.bind('<<TreeviewSelect>>', self.on_expense_select)
        btn_frame = tb.Frame(frame)
        btn_frame.pack(pady=5)
        tb.Button(btn_frame, text='Delete Selected', style='Accent.TButton', command=self.delete_expense).grid(row=0, column=0, padx=5)
        self.load_expenses()

    def save_expense(self):
        date = self.expense_date_var.get().strip()
        typ = self.expense_type_var.get().strip()
        amount = self.expense_amount_var.get().strip()
        desc = self.expense_desc_var.get().strip()
        if not date or not typ or not amount:
            self.set_status('Please fill all required fields.', error=True)
            return
        try:
            amount_val = float(amount)
        except ValueError:
            self.set_status('Amount must be a number.', error=True)
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        if self.expense_edit_id:
            c.execute('UPDATE expenses SET date=?, type=?, amount=?, description=? WHERE id=?', (date, typ, amount_val, desc, self.expense_edit_id))
            self.set_status('Expense updated.')
        else:
            c.execute('INSERT INTO expenses (date, type, amount, description) VALUES (?, ?, ?, ?)', (date, typ, amount_val, desc))
            self.set_status('Expense added.')
        conn.commit()
        conn.close()
        self.expense_date_var.set('')
        self.expense_type_var.set('')
        self.expense_amount_var.set('')
        self.expense_desc_var.set('')
        self.expense_edit_id = None
        self.load_expenses()

    def on_expense_select(self, event):
        selected = self.expenses_tree.selection()
        if not selected:
            self.expense_edit_id = None
            self.expense_date_var.set('')
            self.expense_type_var.set('')
            self.expense_amount_var.set('')
            self.expense_desc_var.set('')
            return
        item = self.expenses_tree.item(selected[0])['values']
        self.expense_edit_id = item[0]
        self.expense_date_var.set(item[1])
        self.expense_type_var.set(item[2])
        self.expense_amount_var.set(item[3])
        self.expense_desc_var.set(item[4])

    def load_expenses(self):
        for row in self.expenses_tree.get_children():
            self.expenses_tree.delete(row)
        search = self.expense_search_var.get().lower() if hasattr(self, 'expense_search_var') else ''
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id, date, type, amount, description FROM expenses ORDER BY id')
        rows = c.fetchall()
        filtered = [row for row in rows if search in str(row[1]).lower() or search in str(row[2]).lower() or search in str(row[4]).lower()]
        self.insert_treeview_rows(self.expenses_tree, filtered)
        conn.close()

    def delete_expense(self):
        selected = self.expenses_tree.selection()
        if not selected:
            self.set_status('Select an expense to delete.', error=True)
            return
        expense_id = self.expenses_tree.item(selected[0])['values'][0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('DELETE FROM expenses WHERE id=?', (expense_id,))
        conn.commit()
        conn.close()
        self.load_expenses()
        self.set_status('Expense deleted.')

    def init_reports_tab(self):
        frame = self.tabs['Reports']
        for widget in frame.winfo_children():
            widget.destroy()
        # Report selection frame
        selection_frame = tb.Frame(frame)
        selection_frame.pack(pady=10, padx=10, fill='x')
        # Report type selection
        tb.Label(selection_frame, text='Report Type:').pack(side='left', padx=5)
        self.report_type_var = tb.StringVar()
        report_types = ['Income Statement', 'Balance Sheet', 'Cash Flow Statement', 'Trial Balance']
        report_cb = tb.Combobox(selection_frame, textvariable=self.report_type_var, values=report_types, state='readonly', width=20)
        report_cb.pack(side='left', padx=5)
        # Date range selection
        date_frame = tb.Frame(frame)
        date_frame.pack(pady=5, padx=10, fill='x')
        tb.Label(date_frame, text='From:').pack(side='left', padx=5)
        self.report_from_var = tb.StringVar()
        tb.Entry(date_frame, textvariable=self.report_from_var, width=12).pack(side='left', padx=5)
        tb.Label(date_frame, text='To:').pack(side='left', padx=5)
        self.report_to_var = tb.StringVar()
        tb.Entry(date_frame, textvariable=self.report_to_var, width=12).pack(side='left', padx=5)
        # Generate button
        tb.Button(frame, text='Generate Report', style='Accent.TButton', command=self.show_report).pack(pady=5)
        # Report display area (set monospace font)
        self.report_text = tb.Text(frame, height=20, width=80, font=('Courier New', 11))
        self.report_text.pack(pady=10, padx=10, fill='both', expand=True)
        # Set default dates
        today = datetime.datetime.now()
        self.report_from_var.set((today - datetime.timedelta(days=30)).strftime('%Y-%m-%d'))
        self.report_to_var.set(today.strftime('%Y-%m-%d'))

    def show_report(self):
        report_type = self.report_type_var.get()
        if not report_type:
            Messagebox.show_warning('Selection Required', 'Please select a report type.')
            return
        
        if report_type == 'Income Statement':
            self.show_income_statement()
        elif report_type == 'Balance Sheet':
            self.show_balance_sheet()
        elif report_type == 'Cash Flow Statement':
            self.show_cash_flow_statement()
        elif report_type == 'Trial Balance':
            self.show_trial_balance()

    def show_income_statement(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        from_date = self.report_from_var.get()
        to_date = self.report_to_var.get()
        # Get total revenues (Income accounts)
        c.execute('SELECT SUM(credit) - SUM(debit) FROM journal_lines WHERE account_id IN (SELECT id FROM accounts WHERE type="Income")')
        total_revenue = c.fetchone()[0] or 0.0
        # Get total operating expenses (Expense accounts, excluding Income Tax)
        c.execute('''
            SELECT SUM(debit) - SUM(credit) FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.type = "Expense" AND a.name NOT LIKE '%Income Tax%'
        ''')
        total_expenses = c.fetchone()[0] or 0.0
        # Get income tax (if any)
        c.execute('''
            SELECT SUM(debit) - SUM(credit) FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.type = "Expense" AND a.name LIKE '%Income Tax%'
        ''')
        income_tax = c.fetchone()[0] or 0.0
        # Net income before tax
        income_before_tax = total_revenue - total_expenses
        # Net income after tax
        net_income = income_before_tax - income_tax
        lines = []
        lines.append('=' * 80)
        lines.append('INCOME STATEMENT'.center(80))
        lines.append('=' * 80)
        lines.append(f'For the period: {from_date} to {to_date}'.center(80))
        lines.append('=' * 80 + '\n')
        lines.append('REVENUE')
        lines.append('-' * 80)
        lines.append(f'{"Description":<40}{"Amount":>30}')
        lines.append(f'{"Total Revenue":<40}{total_revenue:>30.2f}\n')
        lines.append('EXPENSES')
        lines.append('-' * 80)
        lines.append(f'{"Description":<40}{"Amount":>30}')
        lines.append(f'{"Total Expenses":<40}{total_expenses:>30.2f}\n')
        lines.append('NET INCOME')
        lines.append('-' * 80)
        lines.append(f'{"Net Income":<40}{net_income:>30.2f}\n')
        lines.append('=' * 80)
        lines.append('End of Income Statement'.center(80))
        lines.append('=' * 80)
        self.report_text.delete('1.0', tb.END)
        self.report_text.insert(tb.END, '\n'.join(lines))

    def show_balance_sheet(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Get date range
        from_date = self.report_from_var.get()
        to_date = self.report_to_var.get()
        
        # Get current assets (cash, accounts receivable, inventory)
        c.execute('''
            SELECT a.name, SUM(jl.debit), SUM(jl.credit)
            FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.type = 'Asset' 
            AND a.name IN ('Cash', 'Bank', 'Accounts Receivable', 'Inventory')
            GROUP BY a.name
            ORDER BY CASE a.name
                WHEN 'Cash' THEN 1
                WHEN 'Bank' THEN 2
                WHEN 'Accounts Receivable' THEN 3
                WHEN 'Inventory' THEN 4
            END
        ''')
        current_assets = c.fetchall()
        
        # Get fixed assets (equipment, etc.)
        c.execute('''
            SELECT a.name, SUM(jl.debit), SUM(jl.credit)
            FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.type = 'Asset' 
            AND a.name NOT IN ('Cash', 'Bank', 'Accounts Receivable', 'Inventory')
            GROUP BY a.name
            ORDER BY a.name
        ''')
        fixed_assets = c.fetchall()
        
        # Get current liabilities
        c.execute('''
            SELECT a.name, SUM(jl.debit), SUM(jl.credit)
            FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.type = 'Liability' 
            AND a.name = 'Accounts Payable'
            GROUP BY a.name
            ORDER BY a.name
        ''')
        current_liabilities = c.fetchall()
        
        # Get long-term liabilities
        c.execute('''
            SELECT a.name, SUM(jl.debit), SUM(jl.credit)
            FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.type = 'Liability' 
            AND a.name != 'Accounts Payable'
            GROUP BY a.name
            ORDER BY a.name
        ''')
        long_term_liabilities = c.fetchall()
        
        # Get equity accounts
        c.execute('''
            SELECT a.name, SUM(jl.debit), SUM(jl.credit)
            FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.type = 'Equity'
            GROUP BY a.name
            ORDER BY a.name
        ''')
        equity = c.fetchall()
        
        # Calculate totals
        total_current_assets = sum((debit or 0) - (credit or 0) for _, debit, credit in current_assets)
        total_fixed_assets = sum((debit or 0) - (credit or 0) for _, debit, credit in fixed_assets)
        total_assets = total_current_assets + total_fixed_assets
        
        total_current_liabilities = sum((credit or 0) - (debit or 0) for _, debit, credit in current_liabilities)
        total_long_term_liabilities = sum((credit or 0) - (debit or 0) for _, debit, credit in long_term_liabilities)
        total_liabilities = total_current_liabilities + total_long_term_liabilities
        
        total_equity = sum((credit or 0) - (debit or 0) for _, debit, credit in equity)
        
        lines = []
        # Header
        lines.append('=' * 80)
        lines.append('BALANCE SHEET'.center(80))
        lines.append('=' * 80)
        lines.append(f'As of: {to_date}'.center(80))
        lines.append('=' * 80 + '\n')
        
        # Assets Section
        lines.append('ASSETS')
        lines.append('-' * 80)
        
        # Current Assets
        lines.append('Current Assets:')
        for name, debit, credit in current_assets:
            balance = (debit or 0) - (credit or 0)
            lines.append(f'  {name:<28} {balance:>12.2f}')
        lines.append('-' * 80)
        lines.append(f'Total Current Assets: {total_current_assets:>12.2f}\n')
        
        # Fixed Assets
        lines.append('Fixed Assets:')
        for name, debit, credit in fixed_assets:
            balance = (debit or 0) - (credit or 0)
            lines.append(f'  {name:<28} {balance:>12.2f}')
        lines.append('-' * 80)
        lines.append(f'Total Fixed Assets: {total_fixed_assets:>12.2f}')
        lines.append('-' * 80)
        lines.append(f'Total Assets: {total_assets:>12.2f}\n')
        
        # Liabilities Section
        lines.append('LIABILITIES')
        lines.append('-' * 80)
        
        # Current Liabilities
        lines.append('Current Liabilities:')
        for name, debit, credit in current_liabilities:
            balance = (credit or 0) - (debit or 0)
            lines.append(f'  {name:<28} {balance:>12.2f}')
        lines.append('-' * 80)
        lines.append(f'Total Current Liabilities: {total_current_liabilities:>12.2f}\n')
        
        # Long-term Liabilities
        lines.append('Long-term Liabilities:')
        for name, debit, credit in long_term_liabilities:
            balance = (credit or 0) - (debit or 0)
            lines.append(f'  {name:<28} {balance:>12.2f}')
        lines.append('-' * 80)
        lines.append(f'Total Long-term Liabilities: {total_long_term_liabilities:>12.2f}')
        lines.append('-' * 80)
        lines.append(f'Total Liabilities: {total_liabilities:>12.2f}\n')
        
        # Equity Section
        lines.append('EQUITY')
        lines.append('-' * 80)
        for name, debit, credit in equity:
            balance = (credit or 0) - (debit or 0)
            lines.append(f'{name:<30} {balance:>12.2f}')
        lines.append('-' * 80)
        lines.append(f'Total Equity: {total_equity:>12.2f}\n')
        
        # Total Liabilities and Equity
        lines.append('TOTAL LIABILITIES AND EQUITY')
        lines.append('-' * 80)
        lines.append(f'Total: {total_liabilities + total_equity:>12.2f}')
        
        # Footer
        lines.append('\n' + '=' * 80)
        lines.append('End of Balance Sheet'.center(80))
        lines.append('=' * 80)
        
        self.report_text.delete('1.0', tb.END)
        self.report_text.insert(tb.END, '\n'.join(lines))

    def show_cash_flow_statement(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        from_date = self.report_from_var.get()
        to_date = self.report_to_var.get()

        # Net Income
        c.execute('''
            SELECT SUM(credit) - SUM(debit) FROM journal_lines
            WHERE account_id IN (SELECT id FROM accounts WHERE type="Income")
        ''')
        total_income = c.fetchone()[0] or 0.0
        c.execute('''
            SELECT SUM(debit) - SUM(credit) FROM journal_lines
            WHERE account_id IN (SELECT id FROM accounts WHERE type="Expense")
        ''')
        total_expenses = c.fetchone()[0] or 0.0
        net_income = total_income - total_expenses

        # Depreciation & Amortization
        c.execute('''
            SELECT SUM(debit) FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.name LIKE '%Depreciation%' OR a.name LIKE '%Amortization%'
        ''')
        depreciation = c.fetchone()[0] or 0.0

        # Changes in Working Capital
        def get_change(account_name):
            c.execute('''
                SELECT SUM(debit) - SUM(credit) FROM journal_lines jl
                JOIN accounts a ON jl.account_id = a.id
                WHERE a.name = ?
            ''', (account_name,))
            return c.fetchone()[0] or 0.0

        change_ar = get_change('Accounts Receivable')
        change_inv = get_change('Inventory')
        change_ap = get_change('Accounts Payable')
        change_wages = get_change('Salaries and Wages Payable')
        change_gift_card = 0.0  # Decorative, unless you have such an account

        # Correct cash flow logic:
        net_operating = (
            net_income
            + depreciation
            - change_ar      # AR: increase is negative, decrease is positive
            - change_inv     # Inventory: increase is negative, decrease is positive
            + change_ap      # AP: increase is positive, decrease is negative
            + change_wages   # Wages Payable: increase is positive, decrease is negative
            + change_gift_card
        )

        # For reporting, only show nonzero changes, with correct sign and label
        lines = []
        lines.append('CASH FLOWS FROM OPERATING ACTIVITIES')
        lines.append(f'Net Income{"":.<40}{net_income:>10,.0f}')
        lines.append('Adjustments:')
        lines.append(f'+ Depreciation & Amortization{"":.<25}{depreciation:>10,.0f}')
        lines.append('Changes in Working Capital:')
        # AR
        if change_ar > 0:
            lines.append(f'- Increase in Accounts Receivable{"":.<15}{change_ar:>10,.0f}')
        elif change_ar < 0:
            lines.append(f'+ Decrease in Accounts Receivable{"":.<15}{-change_ar:>10,.0f}')
        # Inventory
        if change_inv > 0:
            lines.append(f'- Increase in Inventory{"":.<23}{change_inv:>10,.0f}')
        elif change_inv < 0:
            lines.append(f'+ Decrease in Inventory{"":.<23}{-change_inv:>10,.0f}')
        # AP
        if change_ap > 0:
            lines.append(f'+ Increase in Accounts Payable{"":.<17}{change_ap:>10,.0f}')
        elif change_ap < 0:
            lines.append(f'- Decrease in Accounts Payable{"":.<17}{-change_ap:>10,.0f}')
        # Wages Payable
        if change_wages > 0:
            lines.append(f'+ Increase in Accrued Wages Payable{"":.<7}{change_wages:>10,.0f}')
        elif change_wages < 0:
            lines.append(f'- Decrease in Accrued Wages Payable{"":.<7}{-change_wages:>10,.0f}')
        # Gift Card
        if change_gift_card != 0:
            if change_gift_card > 0:
                lines.append(f'+ Increase in Gift Card Liability{"":.<11}{change_gift_card:>10,.0f}')
            else:
                lines.append(f'- Decrease in Gift Card Liability{"":.<11}{-change_gift_card:>10,.0f}')
        lines.append(f'Net Cash Provided by Operating Activities{"":.<2}{net_operating:>10,.0f}\n')

        # Investing Activities (decorative if not present)
        purchase_equipment = -abs(get_change('Equipment'))  # Negative for purchase
        sale_equipment = abs(get_change('Equipment'))  # Positive for sale
        net_investing = purchase_equipment + sale_equipment

        # Financing Activities (decorative if not present)
        proceeds_loan = 0.0  # Decorative
        repayment_loan = 0.0  # Decorative
        owner_distribution = 0.0  # Decorative
        net_financing = proceeds_loan + repayment_loan + owner_distribution

        # Cash summary
        c.execute('SELECT SUM(debit) - SUM(credit) FROM journal_lines jl JOIN accounts a ON jl.account_id = a.id WHERE a.name = "Cash"')
        cash_end = c.fetchone()[0] or 0.0
        cash_begin = cash_end - (net_operating + net_investing + net_financing)
        net_increase = cash_end - cash_begin

        lines.append('CASH FLOWS FROM INVESTING ACTIVITIES')
        lines.append(f'- Purchase of New Equipment{"":.<22}{purchase_equipment:>10,.0f}')
        lines.append(f'+ Proceeds from Sale of Equipment{"":.<13}{sale_equipment:>10,.0f}')
        lines.append(f'Net Cash Provided by Investing Activities{"":.<5}{net_investing:>10,.0f}\n')

        lines.append('CASH FLOWS FROM FINANCING ACTIVITIES')
        lines.append(f'+ Proceeds from Line of Credit Drawdown{"":.<4}{proceeds_loan:>10,.0f}')
        lines.append(f'- Repayment of Equipment Loan Principal{"":.<2}{repayment_loan:>10,.0f}')
        lines.append(f'- Owner Distribution{"":.<28}{owner_distribution:>10,.0f}')
        lines.append(f'Net Cash Provided by Financing Activities{"":.<5}{net_financing:>10,.0f}\n')

        lines.append(f'NET INCREASE IN CASH{"":.<32}{net_increase:>10,.0f}')
        lines.append(f'CASH AT BEGINNING OF PERIOD{"":.<23}{cash_begin:>10,.0f}')
        lines.append(f'CASH AT END OF PERIOD{"":.<28}{cash_end:>10,.0f}')

        self.report_text.delete('1.0', tb.END)
        self.report_text.insert(tb.END, '\n'.join(lines))

    def show_trial_balance(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        from_date = self.report_from_var.get()
        to_date = self.report_to_var.get()
        # List of accounts in the order from the image
        account_list = [
            'Cash',
            'Accounts Receivable',
            'Supplies',
            'Prepaid Insurance',
            'Equipment',
            'Accumulated Depreciation—Equipment',
            'Notes Payable',
            'Accounts Payable',
            'Unearned Service Revenue',
            'Salaries and Wages Payable',
            'Interest Payable',
            'Common Stock',
            'Retained Earnings',
            'Dividends',
            'Service Revenue',
            'Salaries and Wages Expense',
            'Supplies Expense',
            'Rent Expense',
            'Insurance Expense',
            'Interest Expense',
            'Depreciation Expense',
        ]
        # Get all balances from the database
        c.execute('''
            SELECT a.name, SUM(jl.debit), SUM(jl.credit)
            FROM accounts a
            LEFT JOIN journal_lines jl ON a.id = jl.account_id
            GROUP BY a.name
        ''')
        balances = {row[0]: (row[1] or 0.0, row[2] or 0.0) for row in c.fetchall()}
        conn.close()
        # Table column widths
        col1 = 36  # Account
        col2 = 18  # Debit
        col3 = 18  # Credit
        sep = ' | '
        # Header
        lines = []
        lines.append('=' * (col1 + col2 + col3 + 2 * len(sep)))
        lines.append('ADJUSTED TRIAL BALANCE'.center(col1 + col2 + col3 + 2 * len(sep)))
        lines.append('=' * (col1 + col2 + col3 + 2 * len(sep)))
        lines.append(f'{"Account":<{col1}}{sep}{"Debit":>{col2}}{sep}{"Credit":>{col3}}')
        lines.append('-' * (col1 + col2 + col3 + 2 * len(sep)))
        total_debit = 0.0
        total_credit = 0.0
        for acc in account_list:
            debit, credit = balances.get(acc, (0.0, 0.0))
            # Net balance logic: asset/expense/dividend = debit, liability/equity/revenue = credit
            # For accumulated depreciation, treat as credit (contra-asset)
            if acc == 'Accumulated Depreciation—Equipment':
                net = credit - debit
            else:
                net = debit - credit
            debit_val = net if net > 0 else 0.0
            credit_val = -net if net < 0 else 0.0
            total_debit += debit_val
            total_credit += credit_val
            lines.append(f'{acc:<{col1}}{sep}{debit_val:>{col2}.2f}{sep}{credit_val:>{col3}.2f}')
        lines.append('-' * (col1 + col2 + col3 + 2 * len(sep)))
        lines.append(f'{"TOTALS":<{col1}}{sep}{total_debit:>{col2}.2f}{sep}{total_credit:>{col3}.2f}')
        
        # Add verification message
        if abs(total_debit - total_credit) < 0.01:  # Using small epsilon for floating point comparison
            lines.append('\nVERIFICATION: Debits equal Credits ✓')
        else:
            lines.append('\nVERIFICATION: Debits do not equal Credits! ✗')
            lines.append(f'Difference: {abs(total_debit - total_credit):.2f}')
        
        lines.append('=' * (col1 + col2 + col3 + 2 * len(sep)))
        lines.append('End of Adjusted Trial Balance'.center(col1 + col2 + col3 + 2 * len(sep)))
        lines.append('=' * (col1 + col2 + col3 + 2 * len(sep)))
        self.report_text.delete('1.0', tb.END)
        self.report_text.insert(tb.END, '\n'.join(lines))

    def load_suppliers(self):
        for row in self.suppliers_tree.get_children():
            self.suppliers_tree.delete(row)
        search = self.supplier_search_var.get().lower() if hasattr(self, 'supplier_search_var') else ''
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id, name, contact FROM suppliers ORDER BY id')
        rows = c.fetchall()
        filtered = [row for row in rows if search in str(row[1]).lower() or search in str(row[2]).lower()]
        self.insert_treeview_rows(self.suppliers_tree, filtered)
        conn.close()

    def delete_inventory_item(self):
        selected = self.inventory_tree.selection()
        if not selected:
            self.set_status('Select an inventory item to delete.', error=True)
            return
        item_id = self.inventory_tree.item(selected[0])['values'][0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('DELETE FROM inventory WHERE id=?', (item_id,))
        conn.commit()
        conn.close()
        self.load_inventory()
        self.set_status('Inventory item deleted.')

    def init_menu_tab(self):
        frame = self.tabs['Menu']
        for widget in frame.winfo_children():
            widget.destroy()
        tb.Label(frame, text='Menu Management', style='Section.TLabel').pack(pady=(10, 0))
        
        # Menu Item Entry Form
        entry_frame = tb.Frame(frame)
        entry_frame.pack(pady=10)
        
        # Name
        tb.Label(entry_frame, text='Name:').grid(row=0, column=0, padx=5, pady=5)
        self.menu_name_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.menu_name_var, width=25).grid(row=0, column=1, padx=5, pady=5)
        
        # Description
        tb.Label(entry_frame, text='Description:').grid(row=0, column=2, padx=5, pady=5)
        self.menu_desc_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.menu_desc_var, width=30).grid(row=0, column=3, padx=5, pady=5)
        
        # Price
        tb.Label(entry_frame, text='Price:').grid(row=1, column=0, padx=5, pady=5)
        self.menu_price_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.menu_price_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        
        # Category
        tb.Label(entry_frame, text='Category:').grid(row=1, column=2, padx=5, pady=5)
        self.menu_category_var = tb.StringVar()
        categories = ['Appetizers', 'Main Course', 'Desserts', 'Beverages', 'Specials']
        tb.Combobox(entry_frame, textvariable=self.menu_category_var, values=categories, state='readonly', width=20).grid(row=1, column=3, padx=5, pady=5)
        
        # Preparation Time
        tb.Label(entry_frame, text='Prep Time (mins):').grid(row=2, column=0, padx=5, pady=5)
        self.menu_prep_time_var = tb.StringVar()
        tb.Entry(entry_frame, textvariable=self.menu_prep_time_var, width=10).grid(row=2, column=1, padx=5, pady=5)
        
        # Available
        self.menu_available_var = tb.BooleanVar(value=True)
        tb.Checkbutton(entry_frame, text='Available', variable=self.menu_available_var).grid(row=2, column=2, padx=5, pady=5)
        
        # Buttons
        btn_frame = tb.Frame(entry_frame)
        btn_frame.grid(row=2, column=3, padx=5, pady=5)
        tb.Button(btn_frame, text='Add Item', style='Accent.TButton', command=self.add_menu_item).pack(side='left', padx=5)
        tb.Button(btn_frame, text='Update Item', style='Accent.TButton', command=self.update_menu_item).pack(side='left', padx=5)
        
        # Search
        search_frame = tb.Frame(frame)
        search_frame.pack(pady=(0, 5), padx=10, anchor='w')
        tb.Label(search_frame, text='Search:').pack(side='left')
        self.menu_search_var = tb.StringVar()
        self.menu_search_var.trace('w', lambda *args: self.load_menu_items())
        tb.Entry(search_frame, textvariable=self.menu_search_var, width=20).pack(side='left', padx=5)
        
        # Menu Items Treeview
        self.menu_tree = tb.Treeview(frame, columns=('ID', 'Name', 'Description', 'Price', 'Category', 'Prep Time', 'Available'), 
                                   show='headings', height=12)
        self.menu_tree.heading('ID', text='ID')
        self.menu_tree.heading('Name', text='Name')
        self.menu_tree.heading('Description', text='Description')
        self.menu_tree.heading('Price', text='Price')
        self.menu_tree.heading('Category', text='Category')
        self.menu_tree.heading('Prep Time', text='Prep Time')
        self.menu_tree.heading('Available', text='Available')
        
        self.menu_tree.column('ID', width=40, anchor='center')
        self.menu_tree.column('Name', width=150)
        self.menu_tree.column('Description', width=200)
        self.menu_tree.column('Price', width=80, anchor='e')
        self.menu_tree.column('Category', width=100)
        self.menu_tree.column('Prep Time', width=80, anchor='center')
        self.menu_tree.column('Available', width=80, anchor='center')
        
        self.menu_tree.pack(pady=10, padx=10, fill='x')
        self.style_treeview(self.menu_tree)
        self.menu_tree.bind('<<TreeviewSelect>>', self.on_menu_item_select)
        
        # Delete button
        tb.Button(frame, text='Delete Selected', style='Accent.TButton', command=self.delete_menu_item).pack(pady=5)
        
        self.load_menu_items()

    def add_menu_item(self):
        name = self.menu_name_var.get().strip()
        desc = self.menu_desc_var.get().strip()
        price = self.menu_price_var.get().strip()
        category = self.menu_category_var.get()
        prep_time = self.menu_prep_time_var.get().strip()
        available = self.menu_available_var.get()
        if not name or not price or not category:
            Messagebox.show_warning('Input Error', 'Please fill in all required fields.')
            return
        try:
            price_val = float(price)
            prep_time_val = int(prep_time) if prep_time else 0
        except ValueError:
            Messagebox.show_warning('Input Error', 'Price and preparation time must be numbers.')
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''INSERT INTO menu_items (name, description, price, category, preparation_time, is_available)
                    VALUES (?, ?, ?, ?, ?, ?)''', 
                    (name, desc, price_val, category, prep_time_val, 1 if available else 0))
        # Automatically create inventory item if not exists
        c.execute('SELECT id FROM inventory WHERE name=?', (name,))
        if not c.fetchone():
            sku = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            quantity = random.randint(1, 100)
            cost = round(random.uniform(1.0, 100.0), 2)
            c.execute('INSERT INTO inventory (name, sku, quantity, cost, price) VALUES (?, ?, ?, ?, ?)', (name, sku, quantity, cost, price_val))
        conn.commit()
        conn.close()
        self.clear_menu_form()
        self.load_menu_items()
        self.set_status('Menu item added successfully.')
        self.load_inventory()  # Refresh inventory list

    def update_menu_item(self):
        selected = self.menu_tree.selection()
        if not selected:
            Messagebox.show_warning('Selection Error', 'Please select a menu item to update.')
            return
            
        item_id = self.menu_tree.item(selected[0])['values'][0]
        name = self.menu_name_var.get().strip()
        desc = self.menu_desc_var.get().strip()
        price = self.menu_price_var.get().strip()
        category = self.menu_category_var.get()
        prep_time = self.menu_prep_time_var.get().strip()
        available = self.menu_available_var.get()
        
        if not name or not price or not category:
            Messagebox.show_warning('Input Error', 'Please fill in all required fields.')
            return
            
        try:
            price_val = float(price)
            prep_time_val = int(prep_time) if prep_time else 0
        except ValueError:
            Messagebox.show_warning('Input Error', 'Price and preparation time must be numbers.')
            return
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''UPDATE menu_items 
                    SET name=?, description=?, price=?, category=?, preparation_time=?, is_available=?
                    WHERE id=?''', 
                    (name, desc, price_val, category, prep_time_val, 1 if available else 0, item_id))
        conn.commit()
        conn.close()
        
        self.clear_menu_form()
        self.load_menu_items()
        self.set_status('Menu item updated successfully.')

    def delete_menu_item(self):
        selected = self.menu_tree.selection()
        if not selected:
            Messagebox.show_warning('Selection Error', 'Please select a menu item to delete.')
            return
            
        if not Messagebox.yesno('Confirm Delete', 'Are you sure you want to delete this menu item?'):
            return
            
        item_id = self.menu_tree.item(selected[0])['values'][0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('DELETE FROM menu_items WHERE id=?', (item_id,))
        conn.commit()
        conn.close()
        
        self.clear_menu_form()
        self.load_menu_items()
        self.set_status('Menu item deleted successfully.')

    def on_menu_item_select(self, event):
        selected = self.menu_tree.selection()
        if not selected:
            return
            
        item = self.menu_tree.item(selected[0])['values']
        self.menu_name_var.set(item[1])
        self.menu_desc_var.set(item[2])
        self.menu_price_var.set(item[3])
        self.menu_category_var.set(item[4])
        self.menu_prep_time_var.set(item[5])
        self.menu_available_var.set(item[6] == 'Yes')

    def clear_menu_form(self):
        self.menu_name_var.set('')
        self.menu_desc_var.set('')
        self.menu_price_var.set('')
        self.menu_category_var.set('')
        self.menu_prep_time_var.set('')
        self.menu_available_var.set(True)

    def load_menu_items(self):
        for row in self.menu_tree.get_children():
            self.menu_tree.delete(row)
            
        search = self.menu_search_var.get().lower() if hasattr(self, 'menu_search_var') else ''
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id, name, description, price, category, preparation_time, is_available FROM menu_items ORDER BY category, name')
        rows = c.fetchall()
        
        filtered = [row for row in rows if search in str(row[1]).lower() or search in str(row[2]).lower()]
        
        for row in filtered:
            values = list(row)
            values[3] = f'{values[3]:.2f}'  # Format price
            values[6] = 'Yes' if values[6] else 'No'  # Convert available to Yes/No
            self.menu_tree.insert('', 'end', values=values)
            
        conn.close()

    def init_orders_tab(self):
        frame = self.tabs['Orders']
        for widget in frame.winfo_children():
            widget.destroy()
        tb.Label(frame, text='Place Order', style='Section.TLabel').pack(pady=(10, 0))
        order_entry_frame = tb.Frame(frame)
        order_entry_frame.pack(pady=10)
        # Table selection with refresh button
        table_frame = tb.Frame(order_entry_frame)
        table_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        tb.Label(table_frame, text='Table:').pack(side='left')
        self.order_table_var = tb.StringVar()
        self.load_tables_for_orders()
        self.order_table_cb = tb.Combobox(table_frame, textvariable=self.order_table_var, values=self.tables_for_orders, state='readonly', width=10)
        self.order_table_cb.pack(side='left', padx=5)
        tb.Button(table_frame, text='↻', width=3, command=self.load_tables_for_orders).pack(side='left')
        # Menu item selection with refresh button
        menu_frame = tb.Frame(order_entry_frame)
        menu_frame.grid(row=0, column=2, columnspan=2, padx=5, pady=5)
        tb.Label(menu_frame, text='Menu Item:').pack(side='left')
        self.order_menu_item_var = tb.StringVar()
        self.load_menu_items_for_orders()
        self.order_menu_item_cb = tb.Combobox(menu_frame, textvariable=self.order_menu_item_var, values=self.menu_items_for_orders, state='readonly', width=20)
        self.order_menu_item_cb.pack(side='left', padx=5)
        tb.Button(menu_frame, text='↻', width=3, command=self.load_menu_items_for_orders).pack(side='left')
        # Quantity
        tb.Label(order_entry_frame, text='Qty:').grid(row=0, column=4, padx=5, pady=5)
        self.order_qty_var = tb.StringVar(value='1')
        tb.Entry(order_entry_frame, textvariable=self.order_qty_var, width=5).grid(row=0, column=5, padx=5, pady=5)
        tb.Button(order_entry_frame, text='Add to Order', style='Accent.TButton', command=self.add_item_to_order_cart).grid(row=0, column=6, padx=10, pady=5)
        # Cart
        self.order_cart = []
        self.order_cart_tree = tb.Treeview(frame, columns=('Item', 'Qty', 'Price', 'Total'), show='headings', height=5)
        self.order_cart_tree.heading('Item', text='Item')
        self.order_cart_tree.heading('Qty', text='Qty')
        self.order_cart_tree.heading('Price', text='Price')
        self.order_cart_tree.heading('Total', text='Total')
        self.order_cart_tree.column('Item', width=150)
        self.order_cart_tree.column('Qty', width=50, anchor='center')
        self.order_cart_tree.column('Price', width=80, anchor='e')
        self.order_cart_tree.column('Total', width=80, anchor='e')
        self.order_cart_tree.pack(pady=5, padx=10, fill='x')
        tb.Button(frame, text='Remove Selected from Cart', style='Accent.TButton', command=self.remove_item_from_order_cart).pack(pady=2)
        tb.Button(frame, text='Place Order', style='Accent.TButton', command=self.place_order).pack(pady=5)
        # Orders list
        orders_header = tb.Frame(frame)
        orders_header.pack(fill='x', padx=10, pady=(15, 0))
        tb.Label(orders_header, text='Current & Past Orders', style='Section.TLabel').pack(side='left')
        tb.Button(orders_header, text='Refresh', style='Accent.TButton', command=self.load_orders).pack(side='right')
        self.orders_tree = tb.Treeview(frame, columns=('Order #', 'Table', 'Date', 'Status', 'Total', 'Payment'), show='headings', height=8)
        self.orders_tree.heading('Order #', text='Order #')
        self.orders_tree.heading('Table', text='Table')
        self.orders_tree.heading('Date', text='Date')
        self.orders_tree.heading('Status', text='Status')
        self.orders_tree.heading('Total', text='Total')
        self.orders_tree.heading('Payment', text='Payment')
        self.orders_tree.column('Order #', width=80, anchor='center')
        self.orders_tree.column('Table', width=60, anchor='center')
        self.orders_tree.column('Date', width=120)
        self.orders_tree.column('Status', width=100, anchor='center')
        self.orders_tree.column('Total', width=80, anchor='e')
        self.orders_tree.column('Payment', width=100, anchor='center')
        self.orders_tree.pack(pady=10, padx=10, fill='x')
        self.orders_tree.bind('<<TreeviewSelect>>', self.on_order_select)
        self.load_orders()

    def load_tables_for_orders(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT table_number FROM tables ORDER BY table_number')
        self.tables_for_orders = [str(row[0]) for row in c.fetchall()]
        if hasattr(self, 'order_table_cb'):
            self.order_table_cb['values'] = self.tables_for_orders
        conn.close()

    def load_menu_items_for_orders(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT name FROM menu_items WHERE is_available=1 ORDER BY name')
        self.menu_items_for_orders = [row[0] for row in c.fetchall()]
        if hasattr(self, 'order_menu_item_cb'):
            self.order_menu_item_cb['values'] = self.menu_items_for_orders
        conn.close()

    def add_item_to_order_cart(self):
        item_name = self.order_menu_item_var.get()
        qty = self.order_qty_var.get().strip()
        if not item_name or not qty:
            Messagebox.show_warning('Input Error', 'Select a menu item and quantity.')
            return
        try:
            qty_val = int(qty)
            if qty_val <= 0:
                raise ValueError
        except ValueError:
            Messagebox.show_warning('Input Error', 'Quantity must be a positive integer.')
            return
        # Get price
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT price FROM menu_items WHERE name=?', (item_name,))
        row = c.fetchone()
        conn.close()
        if not row:
            Messagebox.show_warning('Menu Error', 'Menu item not found.')
            return
        price = row[0]
        total = price * qty_val
        self.order_cart.append({'item': item_name, 'qty': qty_val, 'price': price, 'total': total})
        self.refresh_order_cart_tree()

    def refresh_order_cart_tree(self):
        for row in self.order_cart_tree.get_children():
            self.order_cart_tree.delete(row)
        for item in self.order_cart:
            self.order_cart_tree.insert('', 'end', values=(item['item'], item['qty'], f"{item['price']:.2f}", f"{item['total']:.2f}"))

    def remove_item_from_order_cart(self):
        selected = self.order_cart_tree.selection()
        if not selected:
            return
        idx = self.order_cart_tree.index(selected[0])
        del self.order_cart[idx]
        self.refresh_order_cart_tree()

    def place_order(self):
        table = self.order_table_var.get()
        if not table or not self.order_cart:
            Messagebox.show_warning('Input Error', 'Select a table and add at least one item.')
            return

        # Check inventory availability for all items
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        # Track total cost for COGS
        total_cost = 0
        for item in self.order_cart:
            # Get menu item ingredients and costs
            c.execute('''
                SELECT ki.name, ki.quantity, mi.quantity as required_qty, ki.cost_per_unit
                FROM menu_item_ingredients mi
                JOIN kitchen_inventory ki ON mi.inventory_id = ki.id
                WHERE mi.menu_item_id = (
                    SELECT id FROM menu_items WHERE name = ?
                )
            ''', (item['item'],))
            ingredients = c.fetchall()
            item_cost = 0
            for ingredient in ingredients:
                name, available, required, cost = ingredient
                if available < (required * item['qty']):
                    Messagebox.show_warning('Inventory Error', 
                        f'Not enough {name} in inventory for {item["item"]}.')
                    conn.close()
                    return
                item_cost += required * cost * item['qty']
            total_cost += item_cost
        import datetime
        order_number = f"ORD{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        order_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total_amount = sum(item['total'] for item in self.order_cart)
        
        # Create order
        c.execute('INSERT INTO orders (order_number, table_number, order_date, status, total_amount, cost_amount) VALUES (?, ?, ?, ?, ?, ?)',
                  (order_number, table, order_date, 'pending', total_amount, total_cost))
        order_id = c.lastrowid

        # Add order items and update inventory
        for item in self.order_cart:
            c.execute('SELECT id FROM menu_items WHERE name=?', (item['item'],))
            menu_item_id = c.fetchone()[0]
            c.execute('INSERT INTO order_items (order_id, menu_item_id, quantity, price) VALUES (?, ?, ?, ?)',
                      (order_id, menu_item_id, item['qty'], item['price']))
            
            # Update inventory quantities
            c.execute('''
                UPDATE kitchen_inventory
                SET quantity = quantity - (
                    SELECT quantity * ? 
                    FROM menu_item_ingredients 
                    WHERE menu_item_id = ?
                )
                WHERE id IN (
                    SELECT inventory_id 
                    FROM menu_item_ingredients 
                    WHERE menu_item_id = ?
                )
            ''', (item['qty'], menu_item_id, menu_item_id))

        conn.commit()
        conn.close()
        self.order_cart = []
        self.refresh_order_cart_tree()
        self.load_orders()
        self.set_status('Order placed successfully.')

    def load_orders(self):
        for row in self.orders_tree.get_children():
            self.orders_tree.delete(row)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT order_number, table_number, order_date, status, total_amount, payment_status FROM orders ORDER BY id DESC')
        rows = c.fetchall()
        for row in rows:
            values = list(row)
            values[4] = f'{values[4]:.2f}'
            self.orders_tree.insert('', 'end', values=values)
        conn.close()

    def on_order_select(self, event):
        pass  # For future: show order details, allow status update

    def update_order_status(self):
        selected = self.orders_tree.selection()
        if not selected:
            Messagebox.show_warning('Select Order', 'Select an order to update.')
            return
        order_number = self.orders_tree.item(selected[0])['values'][0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT status FROM orders WHERE order_number=?', (order_number,))
        row = c.fetchone()
        if not row:
            conn.close()
            return
        current_status = row[0]
        # Cycle through statuses: pending -> in kitchen -> served -> paid
        status_flow = ['pending', 'in kitchen', 'served', 'paid']
        try:
            idx = status_flow.index(current_status)
            new_status = status_flow[(idx + 1) % len(status_flow)]
        except ValueError:
            new_status = 'pending'
        c.execute('UPDATE orders SET status=? WHERE order_number=?', (new_status, order_number))
        conn.commit()
        conn.close()
        self.load_orders()
        self.set_status(f'Order status updated to {new_status}.')

    def init_kitchen_tab(self):
        frame = self.tabs['Kitchen']
        for widget in frame.winfo_children():
            widget.destroy()
        
        # Title and refresh button
        header_frame = tb.Frame(frame)
        header_frame.pack(fill='x', padx=10, pady=5)
        tb.Label(header_frame, text='Kitchen Orders', style='Section.TLabel').pack(side='left')
        tb.Button(header_frame, text='Refresh', style='Accent.TButton', command=self.load_kitchen_orders).pack(side='right')
        
        # Orders Treeview
        self.kitchen_orders_tree = tb.Treeview(frame, 
            columns=('Order #', 'Table', 'Time', 'Item', 'Qty', 'Status', 'Notes'),
            show='headings', height=15)
        
        self.kitchen_orders_tree.heading('Order #', text='Order #')
        self.kitchen_orders_tree.heading('Table', text='Table')
        self.kitchen_orders_tree.heading('Time', text='Time')
        self.kitchen_orders_tree.heading('Item', text='Item')
        self.kitchen_orders_tree.heading('Qty', text='Qty')
        self.kitchen_orders_tree.heading('Status', text='Status')
        self.kitchen_orders_tree.heading('Notes', text='Notes')
        
        self.kitchen_orders_tree.column('Order #', width=100)
        self.kitchen_orders_tree.column('Table', width=60)
        self.kitchen_orders_tree.column('Time', width=100)
        self.kitchen_orders_tree.column('Item', width=200)
        self.kitchen_orders_tree.column('Qty', width=50)
        self.kitchen_orders_tree.column('Status', width=100)
        self.kitchen_orders_tree.column('Notes', width=150)
        
        self.kitchen_orders_tree.pack(padx=10, pady=5, fill='both', expand=True)
        self.style_treeview(self.kitchen_orders_tree)
        
        # Buttons frame
        btn_frame = tb.Frame(frame)
        btn_frame.pack(pady=10)
        
        tb.Button(btn_frame, text='Mark as Prepared', style='Accent.TButton', 
                 command=self.mark_item_prepared).pack(side='left', padx=5)
        tb.Button(btn_frame, text='Mark Order Complete', style='Accent.TButton',
                 command=self.mark_order_complete).pack(side='left', padx=5)
        
        # Load initial orders
        self.load_kitchen_orders()

    def load_kitchen_orders(self):
        # Clear existing items
        for item in self.kitchen_orders_tree.get_children():
            self.kitchen_orders_tree.delete(item)
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Get all pending and in-kitchen orders with their items
        c.execute('''
            SELECT o.order_number, o.table_number, o.order_date, 
                   mi.name, oi.quantity, oi.status, oi.notes, oi.id
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN menu_items mi ON oi.menu_item_id = mi.id
            WHERE o.status IN ('pending', 'in kitchen')
            ORDER BY o.order_date DESC, o.order_number
        ''')
        
        orders = c.fetchall()
        for order in orders:
            order_num, table, date, item, qty, status, notes, item_id = order
            # Format the date to show only time
            time = date.split(' ')[1] if ' ' in date else date
            
            # Set row color based on status
            tag = 'pending' if status == 'pending' else 'preparing'
            
            self.kitchen_orders_tree.insert('', 'end', 
                values=(order_num, table, time, item, qty, status, notes),
                tags=(tag,),
                iid=str(item_id))  # Use item_id as tree item id for easy reference
        
        # Configure tag colors
        self.kitchen_orders_tree.tag_configure('pending', background='#fff3cd')  # Light yellow
        self.kitchen_orders_tree.tag_configure('preparing', background='#d4edda')  # Light green
        
        conn.close()

    def mark_item_prepared(self):
        selected = self.kitchen_orders_tree.selection()
        if not selected:
            Messagebox.show_warning('Selection Required', 'Please select an item to mark as prepared.')
            return
            
        item_id = selected[0]  # The tree item id is the order_item id
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Update the item status
        c.execute('UPDATE order_items SET status = "prepared" WHERE id = ?', (item_id,))
        
        # Check if all items in the order are prepared
        c.execute('''
            SELECT o.id, COUNT(oi.id), SUM(CASE WHEN oi.status = 'prepared' THEN 1 ELSE 0 END)
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE oi.id = ?
            GROUP BY o.id
        ''', (item_id,))
        
        result = c.fetchone()
        if result:
            order_id, total_items, prepared_items = result
            if total_items == prepared_items:
                # All items are prepared, update order status
                c.execute('UPDATE orders SET status = "in kitchen" WHERE id = ?', (order_id,))
        
        conn.commit()
        conn.close()
        
        self.load_kitchen_orders()
        self.set_status('Item marked as prepared.')

    def mark_order_complete(self):
        selected = self.kitchen_orders_tree.selection()
        if not selected:
            Messagebox.show_warning('Selection Required', 'Please select an item to mark its order as complete.')
            return
            
        item_id = selected[0]  # The tree item id is the order_item id
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Get the order ID for this item
        c.execute('SELECT order_id FROM order_items WHERE id = ?', (item_id,))
        result = c.fetchone()
        if not result:
            conn.close()
            return
            
        order_id = result[0]
        
        # Update all items in the order to prepared
        c.execute('UPDATE order_items SET status = "prepared" WHERE order_id = ?', (order_id,))
        
        # Update order status to served
        c.execute('UPDATE orders SET status = "served" WHERE id = ?', (order_id,))
        
        conn.commit()
        conn.close()
        
        self.load_kitchen_orders()
        self.set_status('Order marked as complete.')

    def init_tables_tab(self):
        frame = self.tabs['Tables']
        for widget in frame.winfo_children():
            widget.destroy()
        
        # Title and controls frame
        header_frame = tb.Frame(frame)
        header_frame.pack(fill='x', padx=10, pady=5)
        tb.Label(header_frame, text='Table Management', style='Section.TLabel').pack(side='left')
        tb.Button(header_frame, text='Refresh', style='Accent.TButton', command=self.load_tables).pack(side='right')
        
        # Add new table frame
        add_frame = tb.LabelFrame(frame, text='Add New Table', style='Section.TLabel')
        add_frame.pack(fill='x', padx=10, pady=5)
        
        tb.Label(add_frame, text='Table Number:').grid(row=0, column=0, padx=5, pady=5)
        self.new_table_num_var = tb.StringVar()
        tb.Entry(add_frame, textvariable=self.new_table_num_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        tb.Label(add_frame, text='Capacity:').grid(row=0, column=2, padx=5, pady=5)
        self.new_table_capacity_var = tb.StringVar()
        tb.Entry(add_frame, textvariable=self.new_table_capacity_var, width=10).grid(row=0, column=3, padx=5, pady=5)
        
        tb.Button(add_frame, text='Add Table', style='Accent.TButton', 
                 command=self.add_table).grid(row=0, column=4, padx=10, pady=5)
        
        # Tables Treeview
        self.tables_tree = tb.Treeview(frame, 
            columns=('Table #', 'Capacity', 'Status', 'Current Order'),
            show='headings', height=15)
        
        self.tables_tree.heading('Table #', text='Table #')
        self.tables_tree.heading('Capacity', text='Capacity')
        self.tables_tree.heading('Status', text='Status')
        self.tables_tree.heading('Current Order', text='Current Order')
        
        self.tables_tree.column('Table #', width=80, anchor='center')
        self.tables_tree.column('Capacity', width=80, anchor='center')
        self.tables_tree.column('Status', width=100, anchor='center')
        self.tables_tree.column('Current Order', width=150)
        
        self.tables_tree.pack(padx=10, pady=5, fill='both', expand=True)
        self.style_treeview(self.tables_tree)
        
        # Table actions frame
        actions_frame = tb.Frame(frame)
        actions_frame.pack(pady=10)
        
        tb.Button(actions_frame, text='Mark as Available', style='Accent.TButton',
                 command=lambda: self.update_table_status('available')).pack(side='left', padx=5)
        tb.Button(actions_frame, text='Mark as Occupied', style='Accent.TButton',
                 command=lambda: self.update_table_status('occupied')).pack(side='left', padx=5)
        tb.Button(actions_frame, text='Mark as Reserved', style='Accent.TButton',
                 command=lambda: self.update_table_status('reserved')).pack(side='left', padx=5)
        tb.Button(actions_frame, text='Delete Table', style='Accent.TButton',
                 command=self.delete_table).pack(side='left', padx=5)
        
        # Load initial tables
        self.load_tables()

    def add_table(self):
        table_num = self.new_table_num_var.get().strip()
        capacity = self.new_table_capacity_var.get().strip()
        
        if not table_num or not capacity:
            Messagebox.show_warning('Input Error', 'Please enter both table number and capacity.')
            return
            
        try:
            table_num = int(table_num)
            capacity = int(capacity)
            if table_num <= 0 or capacity <= 0:
                raise ValueError
        except ValueError:
            Messagebox.show_warning('Input Error', 'Table number and capacity must be positive integers.')
            return
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Check if table number already exists
        c.execute('SELECT id FROM tables WHERE table_number = ?', (table_num,))
        if c.fetchone():
            Messagebox.show_warning('Duplicate Table', 'Table number already exists.')
            conn.close()
            return
            
        # Add new table
        c.execute('INSERT INTO tables (table_number, capacity, status) VALUES (?, ?, ?)',
                 (table_num, capacity, 'available'))
        conn.commit()
        conn.close()
        
        self.new_table_num_var.set('')
        self.new_table_capacity_var.set('')
        self.load_tables()
        self.load_tables_for_orders()  # Refresh table list in Orders tab
        self.set_status('Table added successfully.')

    def load_tables(self):
        # Clear existing items
        for item in self.tables_tree.get_children():
            self.tables_tree.delete(item)
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Get all tables with their current orders
        c.execute('''
            SELECT t.table_number, t.capacity, t.status,
                   o.order_number
            FROM tables t
            LEFT JOIN orders o ON t.table_number = o.table_number 
                AND o.status IN ('pending', 'in kitchen', 'served')
            ORDER BY t.table_number
        ''')
        
        tables = c.fetchall()
        for table in tables:
            table_num, capacity, status, order_num = table
            current_order = order_num if order_num else ''
            
            # Set row color based on status
            tag = status
            
            self.tables_tree.insert('', 'end', 
                values=(table_num, capacity, status, current_order),
                tags=(tag,))
        
        # Configure tag colors
        self.tables_tree.tag_configure('available', background='#d4edda')  # Light green
        self.tables_tree.tag_configure('occupied', background='#f8d7da')  # Light red
        self.tables_tree.tag_configure('reserved', background='#fff3cd')  # Light yellow
        
        conn.close()

    def update_table_status(self, new_status):
        selected = self.tables_tree.selection()
        if not selected:
            Messagebox.show_warning('Selection Required', 'Please select a table to update.')
            return
            
        table_num = self.tables_tree.item(selected[0])['values'][0]
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Check if table has active orders
        if new_status == 'available':
            c.execute('''
                SELECT COUNT(*) FROM orders 
                WHERE table_number = ? AND status IN ('pending', 'in kitchen', 'served')
            ''', (table_num,))
            if c.fetchone()[0] > 0:
                Messagebox.show_warning('Active Orders', 
                    'Cannot mark table as available while it has active orders.')
                conn.close()
                return
        
        # Update table status
        c.execute('UPDATE tables SET status = ? WHERE table_number = ?',
                 (new_status, table_num))
        conn.commit()
        conn.close()
        
        self.load_tables()
        self.set_status(f'Table {table_num} marked as {new_status}.')

    def delete_table(self):
        selected = self.tables_tree.selection()
        if not selected:
            Messagebox.show_warning('Selection Required', 'Please select a table to delete.')
            return
            
        table_num = self.tables_tree.item(selected[0])['values'][0]
        
        if not Messagebox.yesno('Confirm Delete', 
            f'Are you sure you want to delete table {table_num}?'):
            return
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Check if table has any orders
        c.execute('SELECT COUNT(*) FROM orders WHERE table_number = ?', (table_num,))
        if c.fetchone()[0] > 0:
            Messagebox.show_warning('Cannot Delete', 
                'Cannot delete table with existing orders.')
            conn.close()
            return
        
        # Delete table
        c.execute('DELETE FROM tables WHERE table_number = ?', (table_num,))
        conn.commit()
        conn.close()
        
        self.load_tables()
        self.load_tables_for_orders()  # Refresh table list in Orders tab
        self.set_status(f'Table {table_num} deleted successfully.')

    def init_cashier_tab(self):
        frame = self.tabs['Cashier']
        for widget in frame.winfo_children():
            widget.destroy()
        
        # Title and controls frame
        header_frame = tb.Frame(frame)
        header_frame.pack(fill='x', padx=10, pady=5)
        tb.Label(header_frame, text='Cashier Operations', style='Section.TLabel').pack(side='left')
        tb.Button(header_frame, text='Refresh', style='Accent.TButton', command=self.load_unpaid_orders).pack(side='right')
        
        # Split frame for orders and payment
        main_frame = tb.Frame(frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left side - Unpaid Orders
        orders_frame = tb.LabelFrame(main_frame, text='Unpaid Orders', style='Section.TLabel')
        orders_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        self.unpaid_orders_tree = tb.Treeview(orders_frame, 
            columns=('Order #', 'Table', 'Date', 'Items', 'Total'),
            show='headings', height=15)
        
        self.unpaid_orders_tree.heading('Order #', text='Order #')
        self.unpaid_orders_tree.heading('Table', text='Table')
        self.unpaid_orders_tree.heading('Date', text='Date')
        self.unpaid_orders_tree.heading('Items', text='Items')
        self.unpaid_orders_tree.heading('Total', text='Total')
        
        self.unpaid_orders_tree.column('Order #', width=100)
        self.unpaid_orders_tree.column('Table', width=60)
        self.unpaid_orders_tree.column('Date', width=120)
        self.unpaid_orders_tree.column('Items', width=200)
        self.unpaid_orders_tree.column('Total', width=80, anchor='e')
        
        self.unpaid_orders_tree.pack(padx=5, pady=5, fill='both', expand=True)
        self.style_treeview(self.unpaid_orders_tree)
        self.unpaid_orders_tree.bind('<<TreeviewSelect>>', self.on_unpaid_order_select)
        
        # Right side - Payment Processing
        payment_frame = tb.LabelFrame(main_frame, text='Process Payment', style='Section.TLabel')
        payment_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # Order details
        details_frame = tb.Frame(payment_frame)
        details_frame.pack(fill='x', padx=5, pady=5)
        
        tb.Label(details_frame, text='Order Details:', style='Section.TLabel').pack(anchor='w')
        self.order_details_text = tb.Text(details_frame, height=8, width=40)
        self.order_details_text.pack(fill='x', pady=5)
        
        # Payment method
        method_frame = tb.Frame(payment_frame)
        method_frame.pack(fill='x', padx=5, pady=5)
        tb.Label(method_frame, text='Payment Method:').pack(side='left')
        self.payment_method_var = tb.StringVar(value='cash')
        methods = ['cash', 'credit card', 'debit card']
        tb.Combobox(method_frame, textvariable=self.payment_method_var, 
                   values=methods, state='readonly', width=15).pack(side='left', padx=5)
        
        # Amount received
        amount_frame = tb.Frame(payment_frame)
        amount_frame.pack(fill='x', padx=5, pady=5)
        tb.Label(amount_frame, text='Amount Received:').pack(side='left')
        self.amount_received_var = tb.StringVar()
        tb.Entry(amount_frame, textvariable=self.amount_received_var, width=15).pack(side='left', padx=5)
        
        # Process payment button
        tb.Button(payment_frame, text='Process Payment', style='Accent.TButton',
                 command=self.process_payment).pack(pady=10)
        
        # Daily sales summary
        summary_frame = tb.LabelFrame(frame, text='Daily Sales Summary', style='Section.TLabel')
        summary_frame.pack(fill='x', padx=10, pady=5)
        
        self.sales_summary_text = tb.Text(summary_frame, height=6, width=70)
        self.sales_summary_text.pack(padx=5, pady=5)
        
        # Load initial data
        self.load_unpaid_orders()
        self.update_sales_summary()

    def load_unpaid_orders(self):
        # Clear existing items
        for item in self.unpaid_orders_tree.get_children():
            self.unpaid_orders_tree.delete(item)
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Get all unpaid orders
        c.execute('''
            SELECT o.order_number, o.table_number, o.order_date, o.total_amount,
                   GROUP_CONCAT(mi.name || ' x' || oi.quantity)
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN menu_items mi ON oi.menu_item_id = mi.id
            WHERE o.payment_status = 'unpaid'
            GROUP BY o.id
            ORDER BY o.order_date DESC
        ''')
        
        orders = c.fetchall()
        for order in orders:
            order_num, table, date, total, items = order
            # Format the date
            date = date.split(' ')[0] if ' ' in date else date
            
            self.unpaid_orders_tree.insert('', 'end', 
                values=(order_num, table, date, items, f'{total:.2f}'))
        
        conn.close()
        
        # Clear order details
        self.order_details_text.delete('1.0', tb.END)
        self.amount_received_var.set('')

    def on_unpaid_order_select(self, event):
        selected = self.unpaid_orders_tree.selection()
        if not selected:
            return
            
        order_num = self.unpaid_orders_tree.item(selected[0])['values'][0]
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Get detailed order information
        c.execute('''
            SELECT o.order_number, o.table_number, o.order_date, o.total_amount,
                   mi.name, oi.quantity, oi.price, oi.notes
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN menu_items mi ON oi.menu_item_id = mi.id
            WHERE o.order_number = ?
        ''', (order_num,))
        
        items = c.fetchall()
        if not items:
            conn.close()
            return
            
        # Format order details
        details = []
        details.append(f"Order #{items[0][0]}")
        details.append(f"Table: {items[0][1]}")
        details.append(f"Date: {items[0][2]}")
        details.append("\nItems:")
        
        for item in items:
            name, qty, price, notes = item[4:8]
            item_total = qty * price
            details.append(f"{name} x{qty} @ {price:.2f} = {item_total:.2f}")
            if notes:
                details.append(f"   Note: {notes}")
        
        details.append(f"\nTotal: {items[0][3]:.2f}")
        
        # Update order details text
        self.order_details_text.delete('1.0', tb.END)
        self.order_details_text.insert('1.0', '\n'.join(details))
        
        # Set amount received to total
        self.amount_received_var.set(f"{items[0][3]:.2f}")
        
        conn.close()

    def process_payment(self):
        selected = self.unpaid_orders_tree.selection()
        if not selected:
            Messagebox.show_warning('Selection Required', 'Please select an order to process payment.')
            return
            
        order_num = self.unpaid_orders_tree.item(selected[0])['values'][0]
        amount_received = self.amount_received_var.get().strip()
        payment_method = self.payment_method_var.get()
        
        if not amount_received or not payment_method:
            Messagebox.show_warning('Input Error', 'Enter amount received and select payment method.')
            return
            
        try:
            amount_received = float(amount_received)
        except ValueError:
            Messagebox.show_warning('Input Error', 'Amount must be a number.')
            return
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Get order total and cost
        c.execute('SELECT total_amount, cost_amount FROM orders WHERE order_number = ?', (order_num,))
        total_amount, cost_amount = c.fetchone()
        
        if amount_received < total_amount:
            Messagebox.show_warning('Payment Error', 'Amount received is less than total amount.')
            conn.close()
            return
            
        # Update order payment status
        c.execute('UPDATE orders SET payment_status = "paid", payment_method = ? WHERE order_number = ?',
                 (payment_method, order_num))
        
        # Create journal entry for the sale
        c.execute('INSERT INTO journal_entries (date, description) VALUES (?, ?)',
                 (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  f'Sale for Order #{order_num}'))
        entry_id = c.lastrowid
        
        # Get account IDs
        accounts = {}
        for account_name, account_type in [
            ('Sales Revenue', 'Income'),
            ('Cost of Goods Sold', 'Expense'),
            ('Inventory', 'Asset'),
            ('Cash' if payment_method == 'cash' else 'Bank', 'Asset')
        ]:
            c.execute('SELECT id FROM accounts WHERE name = ?', (account_name,))
            account = c.fetchone()
            if not account:
                c.execute('INSERT INTO accounts (name, type) VALUES (?, ?)', (account_name, account_type))
                accounts[account_name] = c.lastrowid
            else:
                accounts[account_name] = account[0]
        
        # Add journal lines
        # 1. Debit Cash/Bank
        c.execute('INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)',
                 (entry_id, accounts['Cash' if payment_method == 'cash' else 'Bank'], total_amount, 0))
        
        # 2. Credit Sales Revenue
        c.execute('INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)',
                 (entry_id, accounts['Sales Revenue'], 0, total_amount))
        
        # 3. Debit COGS
        c.execute('INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)',
                 (entry_id, accounts['Cost of Goods Sold'], cost_amount, 0))
        
        # 4. Credit Inventory
        c.execute('INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)',
                 (entry_id, accounts['Inventory'], 0, cost_amount))
        
        conn.commit()
        conn.close()
        
        # Refresh displays
        self.load_unpaid_orders()
        self.update_sales_summary()
        self.load_ledger()
        self.set_status('Payment processed successfully.')

    def generate_receipt(self, order_num, total_amount, amount_received, payment_method):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Get order details
        c.execute('''
            SELECT o.order_number, o.table_number, o.order_date,
                   mi.name, oi.quantity, oi.price, oi.notes
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN menu_items mi ON oi.menu_item_id = mi.id
            WHERE o.order_number = ?
        ''', (order_num,))
        
        items = c.fetchall()
        if not items:
            conn.close()
            return
            
        # Format receipt
        receipt = []
        receipt.append("=" * 40)
        receipt.append("RESTAURANT RECEIPT")
        receipt.append("=" * 40)
        receipt.append(f"Order #{items[0][0]}")
        receipt.append(f"Table: {items[0][1]}")
        receipt.append(f"Date: {items[0][2]}")
        receipt.append("-" * 40)
        receipt.append("Items:")
        
        for item in items:
            name, qty, price, notes = item[3:7]
            item_total = qty * price
            receipt.append(f"{name} x{qty} @ {price:.2f} = {item_total:.2f}")
            if notes:
                receipt.append(f"   Note: {notes}")
        
        receipt.append("-" * 40)
        receipt.append(f"Total: ${total_amount:.2f}")
        receipt.append(f"Payment Method: {payment_method}")
        receipt.append(f"Amount Received: ${amount_received:.2f}")
        if amount_received > total_amount:
            receipt.append(f"Change: ${(amount_received - total_amount):.2f}")
        receipt.append("=" * 40)
        receipt.append("Thank you for dining with us!")
        receipt.append("=" * 40)
        
        # Show receipt in a new window
        receipt_window = tb.Toplevel(self)
        receipt_window.title("Receipt")
        receipt_window.geometry("400x600")
        
        receipt_text = tb.Text(receipt_window, font=('Courier', 10))
        receipt_text.pack(padx=10, pady=10, fill='both', expand=True)
        receipt_text.insert('1.0', '\n'.join(receipt))
        receipt_text.config(state='disabled')
        
        tb.Button(receipt_window, text="Print Receipt", style='Accent.TButton',
                 command=lambda: self.print_receipt('\n'.join(receipt))).pack(pady=10)
        
        conn.close()

    def print_receipt(self, receipt_text):
        # In a real application, this would send to a printer
        # For now, we'll just show a message
        Messagebox.show_info('Print Receipt', 
            'Receipt would be sent to printer.\n\n' + receipt_text)

    def update_sales_summary(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Get today's date
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # Get sales summary for today
        c.execute('''
            SELECT 
                COUNT(*) as total_orders,
                SUM(total_amount) as total_sales,
                payment_method,
                COUNT(*) as method_count
            FROM orders 
            WHERE date(order_date) = ? AND payment_status = 'paid'
            GROUP BY payment_method
        ''', (today,))
        
        results = c.fetchall()
        
        # Format summary
        summary = []
        summary.append(f"Sales Summary for {today}")
        summary.append("-" * 40)
        
        total_orders = 0
        total_sales = 0
        
        for row in results:
            orders, sales, method, count = row
            total_orders += orders
            total_sales += sales
            summary.append(f"{method.title()}: {count} orders, ${sales:.2f}")
        
        summary.append("-" * 40)
        summary.append(f"Total Orders: {total_orders}")
        summary.append(f"Total Sales: ${total_sales:.2f}")
        
        # Update summary text
        self.sales_summary_text.delete('1.0', tb.END)
        self.sales_summary_text.insert('1.0', '\n'.join(summary))
        
        conn.close()

    def process_purchase(self):
        selected = self.purchases_tree.selection()
        if not selected:
            Messagebox.show_warning('Selection Required', 'Please select a purchase to process.')
            return
            
        purchase_num = self.purchases_tree.item(selected[0])['values'][0]
        amount_paid = self.amount_paid_var.get().strip()
        payment_method = self.payment_method_var.get()
        
        if not amount_paid or not payment_method:
            Messagebox.show_warning('Input Error', 'Enter amount paid and select payment method.')
            return
            
        try:
            amount_paid = float(amount_paid)
        except ValueError:
            Messagebox.show_warning('Input Error', 'Amount must be a number.')
            return
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Get purchase total
        c.execute('SELECT total_amount FROM purchases WHERE purchase_number = ?', (purchase_num,))
        total_amount = c.fetchone()[0]
        
        if amount_paid < total_amount:
            Messagebox.show_warning('Payment Error', 'Amount paid is less than total amount.')
            conn.close()
            return
            
        # Update purchase payment status
        c.execute('UPDATE purchases SET payment_status = "paid", payment_method = ? WHERE purchase_number = ?',
                 (payment_method, purchase_num))
        
        # Create journal entry for the purchase
        c.execute('INSERT INTO journal_entries (date, description) VALUES (?, ?)',
                 (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  f'Purchase #{purchase_num}'))
        entry_id = c.lastrowid
        
        # Get inventory account ID
        c.execute('SELECT id FROM accounts WHERE name = "Inventory"')
        inventory_account = c.fetchone()
        if not inventory_account:
            # Create inventory account if it doesn't exist
            c.execute('INSERT INTO accounts (name, type) VALUES (?, ?)', ('Inventory', 'Asset'))
            inventory_account = (c.lastrowid,)
        
        # Get cash/bank account ID
        account_name = 'Cash' if payment_method == 'Cash' else 'Bank'
        c.execute('SELECT id FROM accounts WHERE name = ?', (account_name,))
        cash_account = c.fetchone()
        if not cash_account:
            # Create cash/bank account if it doesn't exist
            c.execute('INSERT INTO accounts (name, type) VALUES (?, ?)', (account_name, 'Asset'))
            cash_account = (c.lastrowid,)
        
        # Add journal lines
        c.execute('INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)',
                 (entry_id, inventory_account[0], total_amount, 0))  # Debit inventory
        c.execute('INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)',
                 (entry_id, cash_account[0], 0, total_amount))  # Credit cash/bank
        
        # Update inventory quantities
        c.execute('''
            UPDATE kitchen_inventory
            SET quantity = quantity + (
                SELECT quantity 
                FROM purchase_items 
                WHERE purchase_id = (
                    SELECT id FROM purchases WHERE purchase_number = ?
                )
                AND inventory_id = kitchen_inventory.id
            )
            WHERE id IN (
                SELECT inventory_id 
                FROM purchase_items 
                WHERE purchase_id = (
                    SELECT id FROM purchases WHERE purchase_number = ?
                )
            )
        ''', (purchase_num, purchase_num))
        
        conn.commit()
        conn.close()
        
        # Refresh displays
        self.load_purchases()
        self.update_inventory()
        
        self.set_status('Purchase processed successfully.')

    def show_sales_records(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            from_date = self.report_from_var.get()
            to_date = self.report_to_var.get()
            if not from_date or not to_date:
                Messagebox.show_warning('Date Range Required', 'Please select both start and end dates.')
                return
            c.execute('SELECT COUNT(*) FROM orders')
            total_orders = c.fetchone()[0]
            if total_orders == 0:
                self.set_status("No orders found in the database", error=True)
                self.report_text.delete('1.0', tb.END)
                self.report_text.insert('1.0', "No orders found in the database. Please add some orders first.")
                return
            c.execute('''
                SELECT COUNT(*) 
                FROM orders 
                WHERE order_date BETWEEN ? AND ?
                AND payment_status = 'paid'
            ''', (from_date, to_date))
            paid_orders = c.fetchone()[0]
            if paid_orders == 0:
                self.set_status("No paid orders found for the selected period", error=True)
                self.report_text.delete('1.0', tb.END)
                self.report_text.insert('1.0', f"No paid orders found for the period {from_date} to {to_date}")
                return
            c.execute('''
                SELECT 
                    DATE(o.order_date) as sale_date,
                    COUNT(DISTINCT o.id) as num_orders,
                    SUM(o.total_amount) as total_sales,
                    SUM(o.cost_amount) as total_cost,
                    SUM(o.total_amount - o.cost_amount) as gross_profit,
                    GROUP_CONCAT(DISTINCT o.payment_method) as payment_methods
                FROM orders o
                WHERE o.order_date BETWEEN ? AND ?
                AND o.payment_status = 'paid'
                GROUP BY DATE(o.order_date)
                ORDER BY sale_date DESC
            ''', (from_date, to_date))
            daily_sales = c.fetchall()
            c.execute('''
                SELECT 
                    mi.name,
                    mi.category,
                    COUNT(oi.id) as quantity_sold,
                    SUM(oi.quantity * oi.price) as total_revenue,
                    SUM(oi.quantity * mi.cost) as total_cost,
                    SUM(oi.quantity * (oi.price - mi.cost)) as gross_profit
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN menu_items mi ON oi.menu_item_id = mi.id
                WHERE o.order_date BETWEEN ? AND ?
                AND o.payment_status = 'paid'
                GROUP BY mi.id
                ORDER BY total_revenue DESC
            ''', (from_date, to_date))
            item_sales = c.fetchall()
            c.execute('''
                SELECT 
                    payment_method,
                    COUNT(*) as num_transactions,
                    SUM(total_amount) as total_amount
                FROM orders
                WHERE order_date BETWEEN ? AND ?
                AND payment_status = 'paid'
                GROUP BY payment_method
            ''', (from_date, to_date))
            payment_stats = c.fetchall()
            lines = []
            lines.append('SALES RECORDS REPORT')
            lines.append(f'Period: {from_date} to {to_date}')
            lines.append('=' * 100)
            lines.append('\nDAILY SALES SUMMARY')
            lines.append('-' * 100)
            lines.append(f'{"Date":<14}{"Orders":>10}{"Sales":>16}{"Cost":>16}{"Profit":>16}{"Payment Methods":>28}')
            total_orders = 0
            total_sales = 0
            total_cost = 0
            total_profit = 0
            for date, orders, sales, cost, profit, methods in daily_sales:
                lines.append(f'{date:<14}{orders:>10}{sales:>16.2f}{cost:>16.2f}{profit:>16.2f}{methods:>28}')
                total_orders += orders
                total_sales += sales
                total_cost += cost
                total_profit += profit
            lines.append('-' * 100)
            lines.append(f'{"TOTAL":<14}{total_orders:>10}{total_sales:>16.2f}{total_cost:>16.2f}{total_profit:>16.2f}')
            lines.append('\nITEM-WISE SALES ANALYSIS')
            lines.append('-' * 100)
            lines.append(f'{"Item":<32}{"Category":<18}{"Qty":>10}{"Revenue":>16}{"Cost":>16}{"Profit":>16}')
            for name, category, qty, revenue, cost, profit in item_sales:
                lines.append(f'{name:<32}{category:<18}{qty:>10}{revenue:>16.2f}{cost:>16.2f}{profit:>16.2f}')
            lines.append('\nPAYMENT METHOD DISTRIBUTION')
            lines.append('-' * 100)
            lines.append(f'{"Method":<20}{"Transactions":>16}{"Amount":>16}')
            for method, transactions, amount in payment_stats:
                lines.append(f'{method:<20}{transactions:>16}{amount:>16.2f}')
            lines.append('\nSUMMARY STATISTICS')
            lines.append('-' * 100)
            lines.append(f'Total Orders: {total_orders}')
            lines.append(f'Total Sales: {total_sales:.2f}')
            lines.append(f'Total Cost: {total_cost:.2f}')
            lines.append(f'Gross Profit: {total_profit:.2f}')
            lines.append(f'Average Order Value: {total_sales/total_orders:.2f}' if total_orders > 0 else 'Average Order Value: 0.00')
            lines.append(f'Profit Margin: {(total_profit/total_sales*100):.1f}%' if total_sales > 0 else 'Profit Margin: 0.0%')
            self.report_text.delete('1.0', tb.END)
            self.report_text.insert('1.0', '\n'.join(lines))
            self.set_status("Sales report generated successfully")
        except sqlite3.Error as e:
            self.set_status(f"Database error: {str(e)}", error=True)
            Messagebox.show_error('Database Error', f'An error occurred while generating the report: {str(e)}')
        except Exception as e:
            self.set_status(f"Error: {str(e)}", error=True)
            Messagebox.show_error('Error', f'An error occurred while generating the report: {str(e)}')
        finally:
            if 'conn' in locals():
                conn.close()

    def show_income_statement(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        from_date = self.report_from_var.get()
        to_date = self.report_to_var.get()
        # Get total revenues (Income accounts)
        c.execute('SELECT SUM(credit) - SUM(debit) FROM journal_lines WHERE account_id IN (SELECT id FROM accounts WHERE type="Income")')
        total_revenue = c.fetchone()[0] or 0.0
        # Get total operating expenses (Expense accounts, excluding Income Tax)
        c.execute('''
            SELECT SUM(debit) - SUM(credit) FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.type = "Expense" AND a.name NOT LIKE '%Income Tax%'
        ''')
        total_expenses = c.fetchone()[0] or 0.0
        # Get income tax (if any)
        c.execute('''
            SELECT SUM(debit) - SUM(credit) FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.type = "Expense" AND a.name LIKE '%Income Tax%'
        ''')
        income_tax = c.fetchone()[0] or 0.0
        # Net income before tax
        income_before_tax = total_revenue - total_expenses
        # Net income after tax
        net_income = income_before_tax - income_tax
        lines = []
        lines.append('=' * 80)
        lines.append('INCOME STATEMENT'.center(80))
        lines.append('=' * 80)
        lines.append(f'For the period: {from_date} to {to_date}'.center(80))
        lines.append('=' * 80 + '\n')
        lines.append('REVENUE')
        lines.append('-' * 80)
        lines.append(f'{"Description":<40}{"Amount":>30}')
        lines.append(f'{"Total Revenue":<40}{total_revenue:>30.2f}\n')
        lines.append('EXPENSES')
        lines.append('-' * 80)
        lines.append(f'{"Description":<40}{"Amount":>30}')
        lines.append(f'{"Total Expenses":<40}{total_expenses:>30.2f}\n')
        lines.append('NET INCOME')
        lines.append('-' * 80)
        lines.append(f'{"Net Income":<40}{net_income:>30.2f}\n')
        lines.append('=' * 80)
        lines.append('End of Income Statement'.center(80))
        lines.append('=' * 80)
        self.report_text.delete('1.0', tb.END)
        self.report_text.insert(tb.END, '\n'.join(lines))

    def show_balance_sheet(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        from_date = self.report_from_var.get()
        to_date = self.report_to_var.get()
        c.execute('''
            SELECT a.name, SUM(jl.debit), SUM(jl.credit)
            FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.type = 'Asset' 
            AND a.name IN ('Cash', 'Bank', 'Accounts Receivable', 'Inventory')
            GROUP BY a.name
            ORDER BY CASE a.name
                WHEN 'Cash' THEN 1
                WHEN 'Bank' THEN 2
                WHEN 'Accounts Receivable' THEN 3
                WHEN 'Inventory' THEN 4
            END
        ''')
        current_assets = c.fetchall()
        c.execute('''
            SELECT a.name, SUM(jl.debit), SUM(jl.credit)
            FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.type = 'Asset' 
            AND a.name NOT IN ('Cash', 'Bank', 'Accounts Receivable', 'Inventory')
            GROUP BY a.name
            ORDER BY a.name
        ''')
        fixed_assets = c.fetchall()
        c.execute('''
            SELECT a.name, SUM(jl.debit), SUM(jl.credit)
            FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.type = 'Liability' 
            AND a.name = 'Accounts Payable'
            GROUP BY a.name
            ORDER BY a.name
        ''')
        current_liabilities = c.fetchall()
        c.execute('''
            SELECT a.name, SUM(jl.debit), SUM(jl.credit)
            FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.type = 'Liability' 
            AND a.name != 'Accounts Payable'
            GROUP BY a.name
            ORDER BY a.name
        ''')
        long_term_liabilities = c.fetchall()
        c.execute('''
            SELECT a.name, SUM(jl.debit), SUM(jl.credit)
            FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.type = 'Equity'
            GROUP BY a.name
            ORDER BY a.name
        ''')
        equity = c.fetchall()
        total_current_assets = sum((debit or 0) - (credit or 0) for _, debit, credit in current_assets)
        total_fixed_assets = sum((debit or 0) - (credit or 0) for _, debit, credit in fixed_assets)
        total_assets = total_current_assets + total_fixed_assets
        total_current_liabilities = sum((credit or 0) - (debit or 0) for _, debit, credit in current_liabilities)
        total_long_term_liabilities = sum((credit or 0) - (debit or 0) for _, debit, credit in long_term_liabilities)
        total_liabilities = total_current_liabilities + total_long_term_liabilities
        total_equity = sum((credit or 0) - (debit or 0) for _, debit, credit in equity)
        lines = []
        lines.append('=' * 90)
        lines.append('BALANCE SHEET'.center(90))
        lines.append('=' * 90)
        lines.append(f'As of: {to_date}'.center(90))
        lines.append('=' * 90 + '\n')
        lines.append('ASSETS')
        lines.append('-' * 90)
        lines.append('Current Assets:')
        for name, debit, credit in current_assets:
            balance = (debit or 0) - (credit or 0)
            lines.append(f'  {name:<36}{balance:>18.2f}')
        lines.append('-' * 90)
        lines.append(f'Total Current Assets: {total_current_assets:>18.2f}\n')
        lines.append('Fixed Assets:')
        for name, debit, credit in fixed_assets:
            balance = (debit or 0) - (credit or 0)
            lines.append(f'  {name:<36}{balance:>18.2f}')
        lines.append('-' * 90)
        lines.append(f'Total Fixed Assets: {total_fixed_assets:>18.2f}')
        lines.append('-' * 90)
        lines.append(f'Total Assets: {total_assets:>18.2f}\n')
        lines.append('LIABILITIES')
        lines.append('-' * 90)
        lines.append('Current Liabilities:')
        for name, debit, credit in current_liabilities:
            balance = (credit or 0) - (debit or 0)
            lines.append(f'  {name:<36}{balance:>18.2f}')
        lines.append('-' * 90)
        lines.append(f'Total Current Liabilities: {total_current_liabilities:>18.2f}\n')
        lines.append('Long-term Liabilities:')
        for name, debit, credit in long_term_liabilities:
            balance = (credit or 0) - (debit or 0)
            lines.append(f'  {name:<36}{balance:>18.2f}')
        lines.append('-' * 90)
        lines.append(f'Total Long-term Liabilities: {total_long_term_liabilities:>18.2f}')
        lines.append('-' * 90)
        lines.append(f'Total Liabilities: {total_liabilities:>18.2f}\n')
        lines.append('EQUITY')
        lines.append('-' * 90)
        for name, debit, credit in equity:
            balance = (credit or 0) - (debit or 0)
            lines.append(f'{name:<38}{balance:>18.2f}')
        lines.append('-' * 90)
        lines.append(f'Total Equity: {total_equity:>18.2f}\n')
        lines.append('TOTAL LIABILITIES AND EQUITY')
        lines.append('-' * 90)
        lines.append(f'Total: {total_liabilities + total_equity:>18.2f}')
        lines.append('\n' + '=' * 90)
        lines.append('End of Balance Sheet'.center(90))
        lines.append('=' * 90)
        self.report_text.delete('1.0', tb.END)
        self.report_text.insert(tb.END, '\n'.join(lines))

    def show_cash_flow_statement(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        from_date = self.report_from_var.get()
        to_date = self.report_to_var.get()

        # Net Income
        c.execute('''
            SELECT SUM(credit) - SUM(debit) FROM journal_lines
            WHERE account_id IN (SELECT id FROM accounts WHERE type="Income")
        ''')
        total_income = c.fetchone()[0] or 0.0
        c.execute('''
            SELECT SUM(debit) - SUM(credit) FROM journal_lines
            WHERE account_id IN (SELECT id FROM accounts WHERE type="Expense")
        ''')
        total_expenses = c.fetchone()[0] or 0.0
        net_income = total_income - total_expenses

        # Depreciation & Amortization
        c.execute('''
            SELECT SUM(debit) FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.name LIKE '%Depreciation%' OR a.name LIKE '%Amortization%'
        ''')
        depreciation = c.fetchone()[0] or 0.0

        # Changes in Working Capital
        def get_change(account_name):
            c.execute('''
                SELECT SUM(debit) - SUM(credit) FROM journal_lines jl
                JOIN accounts a ON jl.account_id = a.id
                WHERE a.name = ?
            ''', (account_name,))
            return c.fetchone()[0] or 0.0

        change_ar = get_change('Accounts Receivable')
        change_inv = get_change('Inventory')
        change_ap = get_change('Accounts Payable')
        change_wages = get_change('Salaries and Wages Payable')
        change_gift_card = 0.0  # Decorative, unless you have such an account

        # Correct cash flow logic:
        net_operating = (
            net_income
            + depreciation
            - change_ar      # AR: increase is negative, decrease is positive
            - change_inv     # Inventory: increase is negative, decrease is positive
            + change_ap      # AP: increase is positive, decrease is negative
            + change_wages   # Wages Payable: increase is positive, decrease is negative
            + change_gift_card
        )

        # For reporting, only show nonzero changes, with correct sign and label
        lines = []
        lines.append('CASH FLOWS FROM OPERATING ACTIVITIES')
        lines.append(f'Net Income{"":.<40}{net_income:>10,.0f}')
        lines.append('Adjustments:')
        lines.append(f'+ Depreciation & Amortization{"":.<25}{depreciation:>10,.0f}')
        lines.append('Changes in Working Capital:')
        # AR
        if change_ar > 0:
            lines.append(f'- Increase in Accounts Receivable{"":.<15}{change_ar:>10,.0f}')
        elif change_ar < 0:
            lines.append(f'+ Decrease in Accounts Receivable{"":.<15}{-change_ar:>10,.0f}')
        # Inventory
        if change_inv > 0:
            lines.append(f'- Increase in Inventory{"":.<23}{change_inv:>10,.0f}')
        elif change_inv < 0:
            lines.append(f'+ Decrease in Inventory{"":.<23}{-change_inv:>10,.0f}')
        # AP
        if change_ap > 0:
            lines.append(f'+ Increase in Accounts Payable{"":.<17}{change_ap:>10,.0f}')
        elif change_ap < 0:
            lines.append(f'- Decrease in Accounts Payable{"":.<17}{-change_ap:>10,.0f}')
        # Wages Payable
        if change_wages > 0:
            lines.append(f'+ Increase in Accrued Wages Payable{"":.<7}{change_wages:>10,.0f}')
        elif change_wages < 0:
            lines.append(f'- Decrease in Accrued Wages Payable{"":.<7}{-change_wages:>10,.0f}')
        # Gift Card
        if change_gift_card != 0:
            if change_gift_card > 0:
                lines.append(f'+ Increase in Gift Card Liability{"":.<11}{change_gift_card:>10,.0f}')
            else:
                lines.append(f'- Decrease in Gift Card Liability{"":.<11}{-change_gift_card:>10,.0f}')
        lines.append(f'Net Cash Provided by Operating Activities{"":.<2}{net_operating:>10,.0f}\n')

        # Investing Activities (decorative if not present)
        purchase_equipment = -abs(get_change('Equipment'))  # Negative for purchase
        sale_equipment = abs(get_change('Equipment'))  # Positive for sale
        net_investing = purchase_equipment + sale_equipment

        # Financing Activities (decorative if not present)
        proceeds_loan = 0.0  # Decorative
        repayment_loan = 0.0  # Decorative
        owner_distribution = 0.0  # Decorative
        net_financing = proceeds_loan + repayment_loan + owner_distribution

        # Cash summary
        c.execute('SELECT SUM(debit) - SUM(credit) FROM journal_lines jl JOIN accounts a ON jl.account_id = a.id WHERE a.name = "Cash"')
        cash_end = c.fetchone()[0] or 0.0
        cash_begin = cash_end - (net_operating + net_investing + net_financing)
        net_increase = cash_end - cash_begin

        lines.append('CASH FLOWS FROM INVESTING ACTIVITIES')
        lines.append(f'- Purchase of New Equipment{"":.<22}{purchase_equipment:>10,.0f}')
        lines.append(f'+ Proceeds from Sale of Equipment{"":.<13}{sale_equipment:>10,.0f}')
        lines.append(f'Net Cash Provided by Investing Activities{"":.<5}{net_investing:>10,.0f}\n')

        lines.append('CASH FLOWS FROM FINANCING ACTIVITIES')
        lines.append(f'+ Proceeds from Line of Credit Drawdown{"":.<4}{proceeds_loan:>10,.0f}')
        lines.append(f'- Repayment of Equipment Loan Principal{"":.<2}{repayment_loan:>10,.0f}')
        lines.append(f'- Owner Distribution{"":.<28}{owner_distribution:>10,.0f}')
        lines.append(f'Net Cash Provided by Financing Activities{"":.<5}{net_financing:>10,.0f}\n')

        lines.append(f'NET INCREASE IN CASH{"":.<32}{net_increase:>10,.0f}')
        lines.append(f'CASH AT BEGINNING OF PERIOD{"":.<23}{cash_begin:>10,.0f}')
        lines.append(f'CASH AT END OF PERIOD{"":.<28}{cash_end:>10,.0f}')

        self.report_text.delete('1.0', tb.END)
        self.report_text.insert(tb.END, '\n'.join(lines))

    def show_trial_balance(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        from_date = self.report_from_var.get()
        to_date = self.report_to_var.get()
        # List of accounts in the order from the image
        account_list = [
            'Cash',
            'Accounts Receivable',
            'Supplies',
            'Prepaid Insurance',
            'Equipment',
            'Accumulated Depreciation—Equipment',
            'Notes Payable',
            'Accounts Payable',
            'Unearned Service Revenue',
            'Salaries and Wages Payable',
            'Interest Payable',
            'Common Stock',
            'Retained Earnings',
            'Dividends',
            'Service Revenue',
            'Salaries and Wages Expense',
            'Supplies Expense',
            'Rent Expense',
            'Insurance Expense',
            'Interest Expense',
            'Depreciation Expense',
        ]
        # Get all balances from the database
        c.execute('''
            SELECT a.name, SUM(jl.debit), SUM(jl.credit)
            FROM accounts a
            LEFT JOIN journal_lines jl ON a.id = jl.account_id
            GROUP BY a.name
        ''')
        balances = {row[0]: (row[1] or 0.0, row[2] or 0.0) for row in c.fetchall()}
        conn.close()
        # Table column widths
        col1 = 36  # Account
        col2 = 18  # Debit
        col3 = 18  # Credit
        sep = ' | '
        # Header
        lines = []
        lines.append('=' * (col1 + col2 + col3 + 2 * len(sep)))
        lines.append('ADJUSTED TRIAL BALANCE'.center(col1 + col2 + col3 + 2 * len(sep)))
        lines.append('=' * (col1 + col2 + col3 + 2 * len(sep)))
        lines.append(f'{"Account":<{col1}}{sep}{"Debit":>{col2}}{sep}{"Credit":>{col3}}')
        lines.append('-' * (col1 + col2 + col3 + 2 * len(sep)))
        total_debit = 0.0
        total_credit = 0.0
        for acc in account_list:
            debit, credit = balances.get(acc, (0.0, 0.0))
            # Net balance logic: asset/expense/dividend = debit, liability/equity/revenue = credit
            # For accumulated depreciation, treat as credit (contra-asset)
            if acc == 'Accumulated Depreciation—Equipment':
                net = credit - debit
            else:
                net = debit - credit
            debit_val = net if net > 0 else 0.0
            credit_val = -net if net < 0 else 0.0
            total_debit += debit_val
            total_credit += credit_val
            lines.append(f'{acc:<{col1}}{sep}{debit_val:>{col2}.2f}{sep}{credit_val:>{col3}.2f}')
        lines.append('-' * (col1 + col2 + col3 + 2 * len(sep)))
        lines.append(f'{"TOTALS":<{col1}}{sep}{total_debit:>{col2}.2f}{sep}{total_credit:>{col3}.2f}')
        
        # Add verification message
        if abs(total_debit - total_credit) < 0.01:  # Using small epsilon for floating point comparison
            lines.append('\nVERIFICATION: Debits equal Credits ✓')
        else:
            lines.append('\nVERIFICATION: Debits do not equal Credits! ✗')
            lines.append(f'Difference: {abs(total_debit - total_credit):.2f}')
        
        lines.append('=' * (col1 + col2 + col3 + 2 * len(sep)))
        lines.append('End of Adjusted Trial Balance'.center(col1 + col2 + col3 + 2 * len(sep)))
        lines.append('=' * (col1 + col2 + col3 + 2 * len(sep)))
        self.report_text.delete('1.0', tb.END)
        self.report_text.insert(tb.END, '\n'.join(lines))

    def save_inventory_item(self):
        name = self.inv_name_var.get().strip()
        sku = self.inv_sku_var.get().strip()
        qty = self.inv_qty_var.get().strip()
        cost = self.inv_cost_var.get().strip()
        price = self.inv_price_var.get().strip()
        if not name:
            self.set_status('Please enter a name.', error=True)
            return
        try:
            qty_val = int(qty) if qty else 0
            cost_val = float(cost) if cost else 0.0
            price_val = float(price) if price else 0.0
        except ValueError:
            self.set_status('Quantity, Cost, and Price must be numbers.', error=True)
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        # Ensure Inventory Adjustment account exists
        c.execute('SELECT id FROM accounts WHERE name = ?', ('Inventory Adjustment',))
        adj_row = c.fetchone()
        if not adj_row:
            c.execute('INSERT INTO accounts (name, type) VALUES (?, ?)', ('Inventory Adjustment', 'Equity'))
            adj_id = c.lastrowid
        else:
            adj_id = adj_row[0]
        # Get Inventory account id
        c.execute('SELECT id FROM accounts WHERE name = ?', ('Inventory',))
        inv_id = c.fetchone()[0]
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        if self.inv_edit_id:
            # Editing existing item: get old value
            c.execute('SELECT quantity, cost FROM inventory WHERE id=?', (self.inv_edit_id,))
            old_qty, old_cost = c.fetchone()
            old_value = (old_qty or 0) * (old_cost or 0)
            new_value = qty_val * cost_val
            diff = new_value - old_value
            c.execute('UPDATE inventory SET name=?, sku=?, quantity=?, cost=?, price=? WHERE id=?', (name, sku, qty_val, cost_val, price_val, self.inv_edit_id))
            self.set_status('Inventory item updated.')
            if diff != 0:
                c.execute('INSERT INTO journal_entries (date, description) VALUES (?, ?)', (today, f'Inventory adjustment for {name}'))
                entry_id = c.lastrowid
                if diff > 0:
                    # Increase: Debit Inventory, Credit Adjustment
                    c.execute('INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)', (entry_id, inv_id, diff, 0))
                    c.execute('INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)', (entry_id, adj_id, 0, diff))
                else:
                    # Decrease: Credit Inventory, Debit Adjustment
                    c.execute('INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)', (entry_id, inv_id, 0, -diff))
                    c.execute('INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)', (entry_id, adj_id, -diff, 0))
        else:
            c.execute('INSERT INTO inventory (name, sku, quantity, cost, price) VALUES (?, ?, ?, ?, ?)', (name, sku, qty_val, cost_val, price_val))
            self.set_status('Inventory item added.')
            # Journal entry for new inventory
            value = qty_val * cost_val
            if value != 0:
                c.execute('INSERT INTO journal_entries (date, description) VALUES (?, ?)', (today, f'Inventory added: {name}'))
                entry_id = c.lastrowid
                c.execute('INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)', (entry_id, inv_id, value, 0))
                c.execute('INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)', (entry_id, adj_id, 0, value))
        conn.commit()
        conn.close()
        self.inv_name_var.set('')
        self.inv_sku_var.set('')
        self.inv_qty_var.set('')
        self.inv_cost_var.set('')
        self.inv_price_var.set('')
        self.inv_edit_id = None
        self.load_inventory()
        if hasattr(self, 'load_purchase_items_inventory'):
            self.load_purchase_items_inventory()
        self.load_ledger()  # Refresh ledger after inventory change

    def on_inventory_select(self, event):
        selected = self.inventory_tree.selection()
        if not selected:
            self.inv_edit_id = None
            self.inv_name_var.set('')
            self.inv_sku_var.set('')
            self.inv_qty_var.set('')
            self.inv_cost_var.set('')
            self.inv_price_var.set('')
            return
        item = self.inventory_tree.item(selected[0])['values']
        self.inv_edit_id = item[0]
        self.inv_name_var.set(item[1])
        self.inv_sku_var.set(item[2])
        self.inv_qty_var.set(item[3])
        self.inv_cost_var.set(item[4])
        self.inv_price_var.set(item[5])

if __name__ == '__main__':
    init_db()
    app = AISApp()
    app.mainloop() 