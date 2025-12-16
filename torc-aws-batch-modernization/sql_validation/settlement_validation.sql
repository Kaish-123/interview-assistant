-- Settlement Data Quality Validation Queries

-- Query 1: Detect settlement instructions on invalid business days (weekends or holidays)
-- This query finds settlement instructions where the settlement date falls on a weekend
-- (Saturday = 6, Sunday = 0 in SQLite's strftime %w) or on a holiday from the HOLIDAYS table
SELECT 
    si.instruction_id,
    si.settlement_date,
    CASE 
        WHEN CAST(strftime('%w', si.settlement_date) AS INTEGER) = 0 THEN 'Falls on Sunday'
        WHEN CAST(strftime('%w', si.settlement_date) AS INTEGER) = 6 THEN 'Falls on Saturday'
        WHEN h.holiday_date IS NOT NULL THEN h.holiday_name || ' (holiday)'
        ELSE 'Unknown issue'
    END AS issue
FROM SETTLEMENT_INSTRUCTIONS si
LEFT JOIN HOLIDAYS h ON si.settlement_date = h.holiday_date
WHERE 
    CAST(strftime('%w', si.settlement_date) AS INTEGER) IN (0, 6)
    OR h.holiday_date IS NOT NULL;

-- Query 2: Identify counterparties with net settlement obligations exceeding credit limits
-- This query sums up all settlement amounts by counterparty and compares against their credit limits
SELECT 
    cl.counterparty,
    cl.credit_limit,
    cl.current_exposure,
    COALESCE(SUM(si.settlement_amount), 0) AS net_settlement,
    cl.current_exposure + COALESCE(SUM(si.settlement_amount), 0) AS total_exposure,
    (cl.current_exposure + COALESCE(SUM(si.settlement_amount), 0)) - cl.credit_limit AS excess
FROM COUNTERPARTY_LIMITS cl
LEFT JOIN SETTLEMENT_INSTRUCTIONS si ON cl.counterparty = si.counterparty
    AND si.status = 'PENDING'
GROUP BY cl.counterparty, cl.credit_limit, cl.current_exposure
HAVING (cl.current_exposure + COALESCE(SUM(si.settlement_amount), 0)) > cl.credit_limit;


