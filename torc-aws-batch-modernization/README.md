# Trade Settlement Batch Modernization: T+2 Processing Pipeline

## Overview

Capital Markets Solutions is migrating their mainframe batch settlement system to AWS. The legacy system processes end-of-day trade files to calculate settlement obligations under T+2 rules (trade date plus 2 business days). This project builds a modern ETL pipeline using AWS Glue to ingest trades from multiple broker feeds and the internal DB2 trading system, calculate net settlement positions by counterparty and security, and generate settlement instructions.

## File Structure

```
/
├── README.md                          (PROVIDED)
├── data/
│   ├── settlement_db.db              (SQLite with trade data)
│   ├── broker_feeds/
│   │   ├── broker_X_trades_20250108.csv  (PROVIDED)
│   │   └── broker_Y_trades_20250108.csv  (PROVIDED)
│   ├── holidays_2025.csv             (Business day calendar)
│   └── db_schema.sql                 (Table schemas)
├── glue_jobs/
│   ├── settlement_etl.py             (EDIT THIS - Main settlement Glue job)
│   ├── business_day_calculator.py    (PROVIDED - T+2 date utilities)
│   ├── glue_mock_framework.py        (PROVIDED)
│   └── requirements.txt              (PROVIDED)
├── lambda_functions/
│   ├── same_day_settlement_handler.py (EDIT THIS - Lambda for urgent settlements)
│   ├── test_settlement_events.json   (PROVIDED)
│   └── counterparty_api_mock.py      (PROVIDED)
├── sql_validation/
│   ├── settlement_validation.sql     (EDIT THIS - Regulatory validation queries)
│   └── query_executor.py             (PROVIDED)
└── tests/
    ├── test_settlement_etl.py        (PROVIDED)
    ├── test_same_day_handler.py      (PROVIDED)
    └── test_validation_queries.py    (PROVIDED)
```

## How to Run and Test

### Install Dependencies
```bash
pip install -r glue_jobs/requirements.txt
```

### Initialize Database
```bash
python3 data/init_db.py
```

### Run Settlement Glue Job
```bash
python3 glue_jobs/settlement_etl.py
```

### Test Lambda Function with Sample Event
```bash
python3 -c "
import json
from lambda_functions.same_day_settlement_handler import lambda_handler
with open('lambda_functions/test_settlement_events.json') as f:
    event = json.load(f)['urgent_settlement_event']
response = lambda_handler(event, None)
print(json.dumps(response, indent=2))
"
```

### Run SQL Validation Queries
```bash
python3 sql_validation/query_executor.py
```

### Run All Tests
```bash
pytest tests/ -v
```

## Your Tasks

### Task 1: Implement AWS Glue Job for T+2 Settlement Calculation
**File**: `glue_jobs/settlement_etl.py`

Implement the `calculate_settlement_instructions()` function to:
- Calculate settlement date using T+2 business day rules (skip weekends and holidays)
- Use the provided aggregation structure to group trades by settlement date, counterparty, and security
- Calculate net position (sum of buy quantities minus sell quantities)
- Generate settlement instructions with direction (DELIVER if net positive, RECEIVE if net negative)
- Return a list of settlement instructions with all required fields

### Task 2: Build Lambda Function for Same-Day Settlement Exceptions
**File**: `lambda_functions/same_day_settlement_handler.py`

Implement the `lambda_handler()` function to:
- Parse and validate the event payload (trade IDs, counterparty, request type)
- Use the provided `validate_trades()` helper function to check if trade IDs exist in the TRADES table
- Calculate total exposure from trades
- Check credit limits using the provided `check_credit_limit()` API
- Return appropriate approval/rejection response with status code and detailed body
- Handle error cases (missing trades, credit limit exceeded)

### Task 3: Write SQL Validation Queries for Settlement Data Quality
**File**: `sql_validation/settlement_validation.sql`

Write two SQL queries:
- **Query 1**: Detect settlement instructions where the settlement date is not a valid business day (falls on weekend or holiday)
- **Query 2**: Identify counterparties with net settlement obligations exceeding their credit limit

## Database Schema

### TRADES
```sql
CREATE TABLE TRADES (
    trade_id TEXT PRIMARY KEY,
    trade_date TEXT,
    security_symbol TEXT,
    counterparty TEXT,
    side TEXT,  -- 'BUY' or 'SELL'
    quantity REAL,
    price REAL,
    trade_amount REAL,
    source_system TEXT
);
```

### SETTLEMENT_INSTRUCTIONS
```sql
CREATE TABLE SETTLEMENT_INSTRUCTIONS (
    instruction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    counterparty TEXT,
    security_symbol TEXT,
    settlement_date TEXT,
    net_quantity REAL,
    direction TEXT,  -- 'DELIVER' or 'RECEIVE'
    settlement_amount REAL,
    status TEXT
);
```

### COUNTERPARTY_LIMITS
```sql
CREATE TABLE COUNTERPARTY_LIMITS (
    counterparty TEXT PRIMARY KEY,
    credit_limit REAL,
    current_exposure REAL
);
```

### HOLIDAYS
```sql
CREATE TABLE HOLIDAYS (
    holiday_date TEXT PRIMARY KEY,
    holiday_name TEXT
);
```


