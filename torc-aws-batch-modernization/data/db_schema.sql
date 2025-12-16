-- Trade Settlement Database Schema

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

CREATE TABLE COUNTERPARTY_LIMITS (
    counterparty TEXT PRIMARY KEY,
    credit_limit REAL,
    current_exposure REAL
);

CREATE TABLE HOLIDAYS (
    holiday_date TEXT PRIMARY KEY,
    holiday_name TEXT
);


