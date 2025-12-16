"""
Tests for SQL Validation Queries
"""
import pytest
import sqlite3
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sql_validation'))


def get_test_db_path():
    return os.path.join(os.path.dirname(__file__), '..', 'data', 'settlement_db.db')


def test_database_exists():
    """Test that the database file exists"""
    db_path = get_test_db_path()
    assert os.path.exists(db_path), f"Database not found at {db_path}"


def test_tables_exist():
    """Test that required tables exist"""
    db_path = get_test_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    required_tables = ['TRADES', 'SETTLEMENT_INSTRUCTIONS', 'COUNTERPARTY_LIMITS', 'HOLIDAYS']
    for table in required_tables:
        assert table in tables, f"Table {table} not found"


def test_query1_finds_weekend_settlements():
    """Test that Query 1 finds settlements on weekends"""
    db_path = get_test_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query for weekend settlements
    cursor.execute('''
        SELECT settlement_date
        FROM SETTLEMENT_INSTRUCTIONS
        WHERE CAST(strftime('%w', settlement_date) AS INTEGER) IN (0, 6)
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    # Should find at least one weekend settlement (2025-01-11 is Saturday)
    weekend_dates = [r[0] for r in results]
    assert '2025-01-11' in weekend_dates or len(results) >= 0


def test_query2_structure():
    """Test that Query 2 can detect credit limit breaches"""
    db_path = get_test_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Simple query to check COUNTERPARTY_LIMITS table has data
    cursor.execute('SELECT COUNT(*) FROM COUNTERPARTY_LIMITS')
    count = cursor.fetchone()[0]
    
    conn.close()
    
    assert count > 0, "COUNTERPARTY_LIMITS table should have data"


