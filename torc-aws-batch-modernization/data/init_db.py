"""
Initialize the SQLite database with schema and sample data
"""
import sqlite3
import os
import csv


def get_db_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'settlement_db.db')


def get_schema_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'db_schema.sql')


def get_holidays_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'holidays_2025.csv')


def init_database():
    db_path = get_db_path()
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    schema_path = get_schema_path()
    with open(schema_path, 'r') as f:
        schema = f.read()
    cursor.executescript(schema)
    
    # Insert sample trades
    trades = [
        ('T001', '2025-01-08', 'AAPL', 'BROKER_A', 'BUY', 1000, 185.50, 185500.00, 'INTERNAL'),
        ('T002', '2025-01-08', 'AAPL', 'BROKER_A', 'SELL', 300, 185.75, 55725.00, 'INTERNAL'),
        ('T003', '2025-01-08', 'AAPL', 'BROKER_A', 'BUY', 200, 185.60, 37120.00, 'INTERNAL'),
        ('T004', '2025-01-08', 'GOOGL', 'BROKER_B', 'BUY', 500, 142.30, 71150.00, 'INTERNAL'),
        ('T005', '2025-01-08', 'GOOGL', 'BROKER_B', 'SELL', 800, 142.50, 114000.00, 'INTERNAL'),
        ('T456', '2025-01-08', 'TSLA', 'HEDGE_FUND_X', 'BUY', 200, 250.00, 50000.00, 'INTERNAL'),
        ('T457', '2025-01-08', 'TSLA', 'HEDGE_FUND_X', 'BUY', 300, 251.00, 75300.00, 'INTERNAL'),
    ]
    
    cursor.executemany('''
        INSERT INTO TRADES (trade_id, trade_date, security_symbol, counterparty, side, 
                           quantity, price, trade_amount, source_system)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', trades)
    
    # Insert counterparty limits
    limits = [
        ('BROKER_A', 10000000.00, 8500000.00),
        ('BROKER_B', 5000000.00, 1000000.00),
        ('BROKER_X', 2000000.00, 500000.00),
        ('BROKER_Y', 3000000.00, 800000.00),
        ('BROKER_Z', 10000000.00, 8500000.00),
        ('HEDGE_FUND_X', 5000000.00, 3000000.00),
    ]
    
    cursor.executemany('''
        INSERT INTO COUNTERPARTY_LIMITS (counterparty, credit_limit, current_exposure)
        VALUES (?, ?, ?)
    ''', limits)
    
    # Insert holidays
    holidays_path = get_holidays_path()
    with open(holidays_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute('''
                INSERT INTO HOLIDAYS (holiday_date, holiday_name)
                VALUES (?, ?)
            ''', (row['holiday_date'], row['holiday_name']))
    
    # Insert sample settlement instructions with intentional issues for validation
    # SI123 falls on Saturday (2025-01-11)
    # SI156 falls on MLK Day holiday (2025-01-20)
    settlement_instructions = [
        ('BROKER_A', 'AAPL', '2025-01-11', 500, 'DELIVER', 92500.00, 'PENDING'),  # Saturday - invalid
        ('BROKER_B', 'GOOGL', '2025-01-10', 300, 'RECEIVE', 42750.00, 'PENDING'),  # Valid Friday
        ('BROKER_Z', 'MSFT', '2025-01-20', 1000, 'DELIVER', 350000.00, 'PENDING'),  # MLK Day - invalid
        ('BROKER_Z', 'NVDA', '2025-01-13', 400, 'DELIVER', 2000000.00, 'PENDING'),  # Valid, but exceeds limit
    ]
    
    cursor.executemany('''
        INSERT INTO SETTLEMENT_INSTRUCTIONS 
        (counterparty, security_symbol, settlement_date, net_quantity, direction, settlement_amount, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', settlement_instructions)
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized at {db_path}")
    print("Sample data inserted:")
    print(f"  - {len(trades)} trades")
    print(f"  - {len(limits)} counterparty limits")
    print(f"  - Settlement instructions with intentional validation issues")


if __name__ == '__main__':
    init_database()


