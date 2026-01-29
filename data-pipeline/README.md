# Data Pipeline Quality & Delivery System

## Overview
Build a production-ready data pipeline that extracts customer transaction data from a SQLite database (simulating Redshift/Aurora), performs PySpark transformations with data quality checks, and securely delivers the cleaned output to an external partner via SFTP with retry logic.

## File Structure
```
.
├── config/
│   └── config.json              - Configuration parameters
├── data/
│   └── transactions.db          - SQLite database with sample data
├── jars/
│   └── sqlite-jdbc-3.43.0.0.jar - JDBC driver for Spark
├── scripts/
│   └── init_db.py               - Database initialization script
├── src/
│   ├── etl_pipeline.py          - PySpark ETL transformation logic
│   ├── sftp_delivery.py         - SFTP upload with retry logic
│   └── main.py                  - Main pipeline orchestrator
├── tests/
│   ├── conftest.py              - Test configuration
│   ├── test_etl_pipeline.py     - ETL unit tests
│   └── test_sftp_delivery.py    - SFTP unit tests
├── requirements.txt             - Python dependencies
└── QUESTIONS.md                 - Written question answers
```

## How to Run and Test

### Setup and Initialization

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database with sample data:
```bash
python3 scripts/init_db.py
```
This creates a SQLite database at `data/transactions.db` with ~10,000 transactions across 3 tables (customers, transactions, products).

3. Inspect the database (optional):
```bash
sqlite3 data/transactions.db
.tables
SELECT COUNT(*) FROM customers;
SELECT COUNT(*) FROM transactions;
SELECT COUNT(*) FROM products;
.exit
```

### Running the Pipeline

```bash
python3 src/main.py
```
This executes the ETL pipeline followed by SFTP delivery. Output parquet files are written to `output/customer_summary/`.

### Running Tests

```bash
python3 -m pytest tests/ -v
```

## Implementation Details

### ETL Pipeline (`src/etl_pipeline.py`)
- Filters invalid records (null customer IDs, negative amounts, future dates)
- Joins customers, products, and transactions tables
- Calculates aggregated metrics: total_spend, transaction_count, average_order_value
- Handles edge cases: customers with zero transactions, missing product info
- Adds registration_year column for partitioning
- Validates data quality before writing output

### SFTP Delivery (`src/sftp_delivery.py`)
- Implements retry logic with exponential backoff (1s, 2s, 4s)
- Handles both file and directory uploads
- Creates delivery manifest for tracking
- Raises SFTPDeliveryException if all retries are exhausted

## Sample Output

After transformation, each customer will have:
- `customer_id`: Unique customer identifier
- `name`, `email`, `registration_date`: Customer details
- `total_spend`: Sum of all transaction amounts
- `transaction_count`: Number of valid transactions
- `average_order_value`: Average transaction amount
- `registration_year`: Partition column extracted from registration_date

Customers with no transactions will have `total_spend=0`, `transaction_count=0`, and `average_order_value=0`.
