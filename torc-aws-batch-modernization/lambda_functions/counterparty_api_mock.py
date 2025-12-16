"""
Mock Counterparty Credit Check API
Simulates credit limit validation for same-day settlement requests
"""
import sqlite3
import os


def get_db_path():
    """Get database path relative to script location"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, '..', 'data', 'settlement_db.db')


def check_credit_limit(counterparty, additional_exposure):
    """
    Check if counterparty has sufficient credit for additional exposure

    Args:
        counterparty: Counterparty name
        additional_exposure: Additional settlement amount to check

    Returns:
        dict with status and details
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get counterparty limits
    cursor.execute('''
        SELECT credit_limit, current_exposure
        FROM COUNTERPARTY_LIMITS
        WHERE counterparty = ?
    ''', (counterparty,))

    result = cursor.fetchone()
    conn.close()

    if not result:
        return {
            'approved': False,
            'reason': 'Counterparty not found',
            'credit_limit': 0,
            'current_exposure': 0,
            'total_exposure': 0
        }

    credit_limit, current_exposure = result
    total_exposure = current_exposure + additional_exposure

    if total_exposure > credit_limit:
        return {
            'approved': False,
            'reason': 'Credit limit exceeded',
            'credit_limit': credit_limit,
            'current_exposure': current_exposure,
            'additional_exposure': additional_exposure,
            'total_exposure': total_exposure,
            'excess': total_exposure - credit_limit
        }

    return {
        'approved': True,
        'reason': 'Within credit limit',
        'credit_limit': credit_limit,
        'current_exposure': current_exposure,
        'additional_exposure': additional_exposure,
        'total_exposure': total_exposure,
        'available_credit': credit_limit - total_exposure
    }


