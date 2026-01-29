-- HackerRank SQL Solution
-- Problem: Get the first order for customers with multiple orders, ordered by customer name

-- Approach 1: Using Window Function (Recommended - Most Efficient)
SELECT 
    CustomerID,
    CustomerName,
    OrderID,
    OrderDate
FROM (
    SELECT 
        c.CustomerID,
        c.CustomerName,
        o.OrderID,
        o.OrderDate,
        ROW_NUMBER() OVER (
            PARTITION BY c.CustomerID 
            ORDER BY o.OrderDate ASC, o.OrderID ASC
        ) as rn,
        COUNT(*) OVER (PARTITION BY c.CustomerID) as order_count
    FROM Customer c
    INNER JOIN OrderInfo o ON c.CustomerID = o.CustomerID
) ranked_orders
WHERE rn = 1 
    AND order_count > 1
ORDER BY CustomerName;

-- Alternative Approach 2: Using Subquery with MIN (Also valid)
-- This approach first identifies customers with multiple orders,
-- then finds their first order date, and finally joins to get the details
/*
SELECT 
    c.CustomerID,
    c.CustomerName,
    o.OrderID,
    o.OrderDate
FROM Customer c
INNER JOIN OrderInfo o ON c.CustomerID = o.CustomerID
INNER JOIN (
    SELECT 
        CustomerID,
        MIN(OrderDate) as FirstOrderDate,
        COUNT(*) as OrderCount
    FROM OrderInfo
    GROUP BY CustomerID
    HAVING COUNT(*) > 1
) first_orders ON c.CustomerID = first_orders.CustomerID
WHERE o.OrderDate = first_orders.FirstOrderDate
    AND o.OrderID = (
        SELECT MIN(OrderID) 
        FROM OrderInfo o2 
        WHERE o2.CustomerID = c.CustomerID 
            AND o2.OrderDate = first_orders.FirstOrderDate
    )
ORDER BY c.CustomerName;
*/

-- Alternative Approach 3: Using CTE (Clean and Readable)
/*
WITH CustomersWithMultipleOrders AS (
    SELECT CustomerID
    FROM OrderInfo
    GROUP BY CustomerID
    HAVING COUNT(*) > 1
),
FirstOrders AS (
    SELECT 
        o.CustomerID,
        o.OrderID,
        o.OrderDate,
        ROW_NUMBER() OVER (
            PARTITION BY o.CustomerID 
            ORDER BY o.OrderDate ASC, o.OrderID ASC
        ) as rn
    FROM OrderInfo o
    INNER JOIN CustomersWithMultipleOrders cmo ON o.CustomerID = cmo.CustomerID
)
SELECT 
    c.CustomerID,
    c.CustomerName,
    fo.OrderID,
    fo.OrderDate
FROM FirstOrders fo
INNER JOIN Customer c ON fo.CustomerID = c.CustomerID
WHERE fo.rn = 1
ORDER BY c.CustomerName;
*/
