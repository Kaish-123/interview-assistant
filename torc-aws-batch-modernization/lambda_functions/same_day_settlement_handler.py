"""
AWS Lambda Handler for Same-Day Settlement Exceptions
Processes urgent same-day settlement requests from counterparties
"""
import json
import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path

# Add current directory to path for relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from counterparty_api_mock import check_credit_limit


def get_db_path():
    """Get database path relative to script location"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, '..', 'data', 'settlement_db.db')


def validate_trades(cursor, trade_ids, counterparty):
    """
    Validate that trades exist in the database
    Returns (valid, trades_data, error_message)
    """
    if not trade_ids:
        return False, [], "No trade IDs provided"

    # Check if trades exist
    placeholders = ','.join('?' * len(trade_ids))
    query = f"SELECT trade_id, trade_amount FROM TRADES WHERE trade_id IN ({placeholders})"
    cursor.execute(query, trade_ids)
    trades = cursor.fetchall()

    if len(trades) != len(trade_ids):
        found_ids = [t[0] for t in trades]
        missing = [tid for tid in trade_ids if tid not in found_ids]
        return False, [], f"Trades not found: {', '.join(missing)}"

    return True, trades, None


def lambda_handler(event, context):
    """
    Handle same-day settlement requests

    Task 2 Implementation:
    - Parse and validate the event payload (trade IDs, counterparty, request type)
    - Use the provided validate_trades() helper function to check if trade IDs exist in TRADES table
    - Calculate total exposure from trades
    - Check credit limits using the provided check_credit_limit() API
    - Return appropriate approval/rejection response with status code and detailed body
    - Handle error cases (missing trades, credit limit exceeded)
    """
    print(f"[AUDIT] Same-day settlement request: {json.dumps(event)}")

    # Parse and validate the event payload
    request_type = event.get('request_type')
    trade_ids = event.get('trade_ids', [])
    counterparty = event.get('counterparty')
    requested_by = event.get('requested_by')
    reason = event.get('reason')

    # Validate required fields
    if not request_type:
        return {
            'statusCode': 400,
            'body': {
                'status': 'REJECTED',
                'reason': 'Missing required field: request_type'
            }
        }

    if request_type != 'SAME_DAY_SETTLEMENT':
        return {
            'statusCode': 400,
            'body': {
                'status': 'REJECTED',
                'reason': f'Invalid request type: {request_type}'
            }
        }

    if not trade_ids:
        return {
            'statusCode': 400,
            'body': {
                'status': 'REJECTED',
                'reason': 'No trade IDs provided'
            }
        }

    if not counterparty:
        return {
            'statusCode': 400,
            'body': {
                'status': 'REJECTED',
                'reason': 'Missing required field: counterparty'
            }
        }

    # Connect to database and validate trades
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Validate trades exist
        valid, trades_data, error_message = validate_trades(cursor, trade_ids, counterparty)

        if not valid:
            conn.close()
            return {
                'statusCode': 404,
                'body': {
                    'status': 'REJECTED',
                    'reason': error_message
                }
            }

        # Calculate total exposure from trades
        total_exposure = sum(trade[1] for trade in trades_data)

        conn.close()

    except Exception as e:
        return {
            'statusCode': 500,
            'body': {
                'status': 'ERROR',
                'reason': f'Database error: {str(e)}'
            }
        }

    # Check credit limits using the provided API
    credit_check = check_credit_limit(counterparty, total_exposure)

    if not credit_check['approved']:
        # Credit check failed
        if credit_check['reason'] == 'Counterparty not found':
            return {
                'statusCode': 404,
                'body': {
                    'status': 'REJECTED',
                    'reason': f'Counterparty not found: {counterparty}',
                    'credit_check': 'FAILED'
                }
            }
        else:
            # Credit limit exceeded
            return {
                'statusCode': 403,
                'body': {
                    'status': 'REJECTED',
                    'reason': 'Credit limit exceeded',
                    'credit_check': 'FAILED',
                    'credit_limit': credit_check.get('credit_limit', 0),
                    'current_exposure': credit_check.get('current_exposure', 0),
                    'additional_exposure': credit_check.get('additional_exposure', 0),
                    'total_exposure': credit_check.get('total_exposure', 0),
                    'excess': credit_check.get('excess', 0)
                }
            }

    # All checks passed - approve the same-day settlement
    # Update settlement dates to today
    today = datetime.now().strftime('%Y-%m-%d')

    return {
        'statusCode': 200,
        'body': {
            'status': 'APPROVED',
            'trades_updated': len(trade_ids),
            'credit_check': 'PASSED',
            'settlement_date': today,
            'counterparty': counterparty,
            'total_exposure': total_exposure,
            'available_credit': credit_check.get('available_credit', 0),
            'requested_by': requested_by,
            'reason': reason
        }
    }


