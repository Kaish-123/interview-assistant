-- Alternative Solution using Window Function
-- Try this if the subquery version doesn't work

SELECT 
    CustomerID,
    CustomerName,
    OrderID,
    OrderDate
FROM (
    SELECT 
        Customer.CustomerID,
        Customer.CustomerName,
        OrderInfo.OrderID,
        OrderInfo.OrderDate,
        ROW_NUMBER() OVER (
            PARTITION BY Customer.CustomerID 
            ORDER BY OrderInfo.OrderDate ASC, OrderInfo.OrderID ASC
        ) AS rn
    FROM Customer
    INNER JOIN OrderInfo ON Customer.CustomerID = OrderInfo.CustomerID
    WHERE Customer.CustomerID IN (
        SELECT CustomerID
        FROM OrderInfo
        GROUP BY CustomerID
        HAVING COUNT(*) > 1
    )
) AS ranked_orders
WHERE rn = 1
ORDER BY CustomerName;
