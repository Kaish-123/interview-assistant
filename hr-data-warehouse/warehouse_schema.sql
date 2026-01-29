-- Analytics Data Warehouse Schema
-- Target table for consolidated employee data

DROP TABLE IF EXISTS employee_analytics;

CREATE TABLE employee_analytics (
    employee_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    department TEXT NOT NULL,
    hire_date TEXT,
    employment_status TEXT,
    base_salary REAL NOT NULL,
    bonus REAL,
    total_compensation REAL,
    performance_score REAL,
    performance_category TEXT,
    review_date TEXT,
    load_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
