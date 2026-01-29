# HR Data Warehouse ETL Design Challenge

## Overview

This project implements a robust ETL (Extract, Transform, Load) solution to consolidate employee data from multiple source systems (HRIS, payroll, performance management) into a centralized analytics data warehouse.

## Project Structure

```
hr-data-warehouse/
├── data_integration.py          # Main ETL pipeline implementation
├── source_systems/
│   ├── hris_extract.csv         # HRIS master data
│   ├── payroll_extract.csv      # Payroll data
│   └── perf_mgmt_extract.csv    # Performance management data
├── target_warehouse.db          # SQLite analytics data warehouse
├── warehouse_schema.sql         # Database schema definition
├── test_integration.py          # Test suite
├── QUESTIONS.md                 # Written questions and answers
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Features

- **Multi-Source Integration**: Consolidates data from three different source systems
- **Data Quality Handling**: Manages missing records, null values, and data validation
- **Incremental Load Support**: Designed to prevent duplicate loads
- **Error Handling**: Comprehensive logging and error tracking
- **Test Coverage**: Full test suite for validation

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## Installation

1. Install dependencies:
```bash
pip3 install -r requirements.txt
```

2. Initialize the data warehouse:
```bash
sqlite3 target_warehouse.db < warehouse_schema.sql
```

## Usage

### Run the ETL Pipeline

```bash
python3 data_integration.py
```

### Inspect the Database

```bash
sqlite3 target_warehouse.db
```

Once inside SQLite shell:
```sql
.schema employee_analytics       -- View table schema
SELECT * FROM employee_analytics LIMIT 5;
.quit
```

### Run Tests

```bash
python3 -m pytest test_integration.py -v
```

## ETL Process

### Extract
- Reads data from three CSV source files:
  - `hris_extract.csv` (master source)
  - `payroll_extract.csv`
  - `perf_mgmt_extract.csv`

### Transform
- Performs left joins to merge all sources (preserving all HRIS records)
- Sets default values for missing optional fields (bonus=0 if null)
- Calculates derived fields:
  - `total_compensation = base_salary + bonus`
  - `performance_category` (derived from performance_score)
- Handles null values appropriately

### Load
- Clears existing data to prevent duplicates
- Inserts transformed records into `employee_analytics` table
- Tracks load statistics and errors

## Data Model

### Source Systems

**HRIS (Human Resources Information System)**
- `employee_id` (Primary Key)
- `full_name`
- `department`
- `hire_date`
- `employment_status`

**Payroll System**
- `employee_id` (Foreign Key)
- `base_salary`
- `bonus` (optional)

**Performance Management System**
- `employee_id` (Foreign Key)
- `performance_score`
- `review_date`

### Target Warehouse: employee_analytics

| Column | Type | Description |
|--------|------|-------------|
| employee_id | INTEGER | Primary key |
| full_name | TEXT | Employee full name |
| department | TEXT | Department name |
| hire_date | TEXT | Hire date |
| employment_status | TEXT | Active/Inactive |
| base_salary | REAL | Base salary |
| bonus | REAL | Bonus amount |
| total_compensation | REAL | Calculated: base_salary + bonus |
| performance_score | REAL | Performance rating |
| performance_category | TEXT | Categorized performance |
| review_date | TEXT | Last review date |
| load_timestamp | TEXT | ETL load timestamp |

## Error Handling

- All errors are logged to `error_log.txt`
- Failed records are tracked in statistics
- Pipeline continues processing even if individual records fail

## Testing

The test suite validates:
- Data extraction from all sources
- Data merging logic (left joins)
- Total compensation calculation
- Default value handling
- Database loading
- Duplicate prevention
- Data quality requirements

## Written Questions

See `QUESTIONS.md` for detailed answers to:
- Informatica PowerCenter workflow design
- Incremental load strategies
- Production deployment considerations

## Author

Lead Software Engineer - PeopleAnalytics Corp.

## License

This project is part of a technical assessment challenge.
