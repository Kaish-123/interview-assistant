"""
Tests for Settlement ETL Job
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'glue_jobs'))

from business_day_calculator import BusinessDayCalculator
from settlement_etl import calculate_settlement_instructions


class MockBusinessDayCalculator:
    """Mock calculator for testing"""
    def calculate_t_plus_2(self, trade_date):
        # Simple mock: just return a fixed date for testing
        return '2025-01-10'


def test_calculate_settlement_instructions_basic():
    """Test basic settlement instruction calculation"""
    trades = [
        {'trade_id': 'T001', 'trade_date': '2025-01-08', 'security_symbol': 'AAPL',
         'counterparty': 'BROKER_A', 'side': 'BUY', 'quantity': 1000, 'price': 185.50, 'trade_amount': 185500.00},
        {'trade_id': 'T002', 'trade_date': '2025-01-08', 'security_symbol': 'AAPL',
         'counterparty': 'BROKER_A', 'side': 'SELL', 'quantity': 300, 'price': 185.75, 'trade_amount': 55725.00},
        {'trade_id': 'T003', 'trade_date': '2025-01-08', 'security_symbol': 'AAPL',
         'counterparty': 'BROKER_A', 'side': 'BUY', 'quantity': 200, 'price': 185.60, 'trade_amount': 37120.00},
    ]
    
    calculator = MockBusinessDayCalculator()
    instructions = calculate_settlement_instructions(trades, calculator)
    
    # Should produce one instruction for BROKER_A/AAPL
    assert len(instructions) == 1
    
    instruction = instructions[0]
    assert instruction['counterparty'] == 'BROKER_A'
    assert instruction['security_symbol'] == 'AAPL'
    assert instruction['net_quantity'] == 900  # 1000 + 200 - 300 = 900
    assert instruction['direction'] == 'DELIVER'  # Net positive = DELIVER
    assert instruction['status'] == 'PENDING'


def test_calculate_settlement_instructions_receive_direction():
    """Test that net negative results in RECEIVE direction"""
    trades = [
        {'trade_id': 'T001', 'trade_date': '2025-01-08', 'security_symbol': 'GOOGL',
         'counterparty': 'BROKER_B', 'side': 'BUY', 'quantity': 500, 'price': 142.30, 'trade_amount': 71150.00},
        {'trade_id': 'T002', 'trade_date': '2025-01-08', 'security_symbol': 'GOOGL',
         'counterparty': 'BROKER_B', 'side': 'SELL', 'quantity': 800, 'price': 142.50, 'trade_amount': 114000.00},
    ]
    
    calculator = MockBusinessDayCalculator()
    instructions = calculate_settlement_instructions(trades, calculator)
    
    assert len(instructions) == 1
    
    instruction = instructions[0]
    assert instruction['counterparty'] == 'BROKER_B'
    assert instruction['security_symbol'] == 'GOOGL'
    assert instruction['net_quantity'] == 300  # abs(500 - 800) = 300
    assert instruction['direction'] == 'RECEIVE'  # Net negative = RECEIVE


def test_calculate_settlement_instructions_multiple_securities():
    """Test aggregation across multiple securities"""
    trades = [
        {'trade_id': 'T001', 'trade_date': '2025-01-08', 'security_symbol': 'AAPL',
         'counterparty': 'BROKER_A', 'side': 'BUY', 'quantity': 100, 'price': 185.00, 'trade_amount': 18500.00},
        {'trade_id': 'T002', 'trade_date': '2025-01-08', 'security_symbol': 'GOOGL',
         'counterparty': 'BROKER_A', 'side': 'BUY', 'quantity': 50, 'price': 142.00, 'trade_amount': 7100.00},
    ]
    
    calculator = MockBusinessDayCalculator()
    instructions = calculate_settlement_instructions(trades, calculator)
    
    # Should produce two instructions (one for each security)
    assert len(instructions) == 2
    
    securities = {inst['security_symbol'] for inst in instructions}
    assert securities == {'AAPL', 'GOOGL'}


def test_calculate_settlement_instructions_zero_net():
    """Test that zero net positions are excluded"""
    trades = [
        {'trade_id': 'T001', 'trade_date': '2025-01-08', 'security_symbol': 'MSFT',
         'counterparty': 'BROKER_C', 'side': 'BUY', 'quantity': 500, 'price': 400.00, 'trade_amount': 200000.00},
        {'trade_id': 'T002', 'trade_date': '2025-01-08', 'security_symbol': 'MSFT',
         'counterparty': 'BROKER_C', 'side': 'SELL', 'quantity': 500, 'price': 400.00, 'trade_amount': 200000.00},
    ]
    
    calculator = MockBusinessDayCalculator()
    instructions = calculate_settlement_instructions(trades, calculator)
    
    # Should produce no instructions since net is zero
    assert len(instructions) == 0


def test_business_day_calculator_weekend_skip():
    """Test that business day calculator skips weekends"""
    # Create calculator without holidays for simplicity
    calculator = BusinessDayCalculator()
    
    # Friday 2025-01-03 + 2 business days = Tuesday 2025-01-07 (skips Sat/Sun)
    result = calculator.add_business_days('2025-01-03', 2)
    assert result == '2025-01-07'


def test_business_day_calculator_t_plus_2():
    """Test T+2 calculation"""
    calculator = BusinessDayCalculator()
    
    # Wednesday 2025-01-08 + 2 business days = Friday 2025-01-10
    result = calculator.calculate_t_plus_2('2025-01-08')
    assert result == '2025-01-10'


