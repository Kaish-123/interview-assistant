"""
Tests for Same-Day Settlement Lambda Handler
"""
import pytest
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda_functions'))


def test_lambda_handler_missing_request_type():
    """Test that missing request_type returns 400"""
    from same_day_settlement_handler import lambda_handler
    
    event = {
        'trade_ids': ['T001'],
        'counterparty': 'BROKER_A'
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    assert response['body']['status'] == 'REJECTED'


def test_lambda_handler_invalid_request_type():
    """Test that invalid request_type returns 400"""
    from same_day_settlement_handler import lambda_handler
    
    event = {
        'request_type': 'INVALID_TYPE',
        'trade_ids': ['T001'],
        'counterparty': 'BROKER_A'
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    assert response['body']['status'] == 'REJECTED'


def test_lambda_handler_missing_trade_ids():
    """Test that missing trade_ids returns 400"""
    from same_day_settlement_handler import lambda_handler
    
    event = {
        'request_type': 'SAME_DAY_SETTLEMENT',
        'counterparty': 'BROKER_A'
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    assert response['body']['status'] == 'REJECTED'


def test_lambda_handler_missing_counterparty():
    """Test that missing counterparty returns 400"""
    from same_day_settlement_handler import lambda_handler
    
    event = {
        'request_type': 'SAME_DAY_SETTLEMENT',
        'trade_ids': ['T001']
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    assert response['body']['status'] == 'REJECTED'


