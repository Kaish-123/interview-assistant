"""
AWS Glue Job for T+2 Settlement Calculation
Processes trade data and generates settlement instructions
"""
import sqlite3
import csv
import os
from collections import defaultdict
from business_day_calculator import BusinessDayCalculator
from glue_mock_framework import get_glue_context


def get_db_path():
    """Get database path relative to script location"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, '..', 'data', 'settlement_db.db')


def get_holidays_path():
    """Get holidays file path"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, '..', 'data', 'holidays_2025.csv')


def get_broker_feeds_dir():
    """Get broker feeds directory path"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, '..', 'data', 'broker_feeds')


def read_trades_from_db(db_path):
    """Read trades from the internal TRADES table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT trade_id, trade_date, security_symbol, counterparty, side, quantity,
               price, trade_amount
        FROM TRADES
    ''')

    trades = []
    for row in cursor.fetchall():
        trades.append({
            'trade_id': row[0],
            'trade_date': row[1],
            'security_symbol': row[2],
            'counterparty': row[3],
            'side': row[4],
            'quantity': row[5],
            'price': row[6],
            'trade_amount': row[7]
        })

    conn.close()
    return trades


def read_trades_from_broker_feeds(broker_feeds_dir):
    """Read trades from broker CSV files"""
    trades = []

    if not os.path.exists(broker_feeds_dir):
        return trades

    for filename in os.listdir(broker_feeds_dir):
        if filename.endswith('.csv'):
            filepath = os.path.join(broker_feeds_dir, filename)
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    trades.append({
                        'trade_id': row['trade_id'],
                        'trade_date': row['trade_date'],
                        'security_symbol': row['security_symbol'],
                        'counterparty': row['counterparty'],
                        'side': row['side'],
                        'quantity': float(row['quantity']),
                        'price': float(row['price']),
                        'trade_amount': float(row['trade_amount'])
                    })

    return trades


def calculate_settlement_instructions(trades, business_day_calculator):
    """
    Calculate settlement instructions from trades

    Task 1 Implementation:
    - Calculate settlement date using T+2 business day rules (skip weekends and holidays)
    - Use the provided aggregation structure to group trades by settlement date, counterparty, and security
    - Calculate net position (sum of buy quantities minus sell quantities)
    - Generate settlement instructions with direction (DELIVER if net positive, RECEIVE if net negative)
    - Return a list of settlement instructions with all required fields
    """
    instructions = []

    # Aggregation structure to help you organize trades
    # Key: (settlement_date, counterparty, security_symbol)
    # Value: {'buy_qty': 0, 'sell_qty': 0, 'buy_amount': 0, 'sell_amount': 0}
    settlements = {}

    # Loop through trades, calculate T+2 settlement date, and aggregate by key
    for trade in trades:
        # Calculate T+2 settlement date
        settlement_date = business_day_calculator.calculate_t_plus_2(trade['trade_date'])
        
        # Create aggregation key
        key = (settlement_date, trade['counterparty'], trade['security_symbol'])
        
        # Initialize if key doesn't exist
        if key not in settlements:
            settlements[key] = {
                'buy_qty': 0,
                'sell_qty': 0,
                'buy_amount': 0,
                'sell_amount': 0
            }
        
        # Aggregate based on trade side
        if trade['side'].upper() == 'BUY':
            settlements[key]['buy_qty'] += trade['quantity']
            settlements[key]['buy_amount'] += trade['trade_amount']
        elif trade['side'].upper() == 'SELL':
            settlements[key]['sell_qty'] += trade['quantity']
            settlements[key]['sell_amount'] += trade['trade_amount']

    # Convert aggregated data to settlement instructions list
    for (settlement_date, counterparty, security_symbol), data in settlements.items():
        # Calculate net position (buy - sell)
        net_quantity = data['buy_qty'] - data['sell_qty']
        net_amount = data['buy_amount'] - data['sell_amount']
        
        # Skip if net quantity is zero (positions cancel out)
        if net_quantity == 0:
            continue
        
        # Determine direction: DELIVER if net positive (we bought more), RECEIVE if net negative
        if net_quantity > 0:
            direction = 'DELIVER'
        else:
            direction = 'RECEIVE'
            net_quantity = abs(net_quantity)
            net_amount = abs(net_amount)
        
        # Create settlement instruction
        instruction = {
            'counterparty': counterparty,
            'security_symbol': security_symbol,
            'settlement_date': settlement_date,
            'net_quantity': net_quantity,
            'direction': direction,
            'settlement_amount': net_amount,
            'status': 'PENDING'
        }
        
        instructions.append(instruction)

    return instructions


def save_settlement_instructions(instructions, db_path):
    """Save settlement instructions to database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for instruction in instructions:
        cursor.execute('''
            INSERT INTO SETTLEMENT_INSTRUCTIONS
            (counterparty, security_symbol, settlement_date, net_quantity, direction,
             settlement_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            instruction['counterparty'],
            instruction['security_symbol'],
            instruction['settlement_date'],
            instruction['net_quantity'],
            instruction['direction'],
            instruction['settlement_amount'],
            instruction['status']
        ))

    conn.commit()
    conn.close()


def main():
    """Main ETL job execution"""
    glue_context = get_glue_context()
    logger = glue_context.get_logger()

    logger.info("Starting T+2 Settlement ETL Job")

    # Initialize business day calculator
    holidays_path = get_holidays_path()
    business_day_calculator = BusinessDayCalculator(holidays_path)
    logger.info(f"Loaded holidays from {holidays_path}")

    # Read trades from internal database
    db_path = get_db_path()
    db_trades = read_trades_from_db(db_path)
    logger.info(f"Read {len(db_trades)} trades from internal database")

    # Read trades from broker feeds
    broker_feeds_dir = get_broker_feeds_dir()
    broker_trades = read_trades_from_broker_feeds(broker_feeds_dir)
    logger.info(f"Read {len(broker_trades)} trades from broker feeds")

    # Combine all trades
    all_trades = db_trades + broker_trades
    logger.info(f"Total trades to process: {len(all_trades)}")

    # Calculate settlement instructions
    instructions = calculate_settlement_instructions(all_trades, business_day_calculator)
    logger.info(f"Generated {len(instructions)} settlement instructions")

    # Save to database
    save_settlement_instructions(instructions, db_path)
    logger.info("Settlement instructions saved to database")

    # Print summary
    print("\n=== Settlement Instructions Summary ===")
    for instruction in instructions:
        print(f"Counterparty: {instruction['counterparty']}, "
              f"Security: {instruction['security_symbol']}, "
              f"Settlement Date: {instruction['settlement_date']}, "
              f"Net Quantity: {instruction['net_quantity']}, "
              f"Direction: {instruction['direction']}")

    logger.info("T+2 Settlement ETL Job completed successfully")


if __name__ == '__main__':
    main()


