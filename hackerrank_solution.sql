-- HackerRank Solution - Fixed Version
-- Problem: Get first order for customers with multiple orders, ordered by customer name

SELECT 
    Customer.CustomerID,
    Customer.CustomerName,
    OrderInfo.OrderID,
    OrderInfo.OrderDate
FROM Customer
INNER JOIN OrderInfo ON Customer.CustomerID = OrderInfo.CustomerID
INNER JOIN (
    SELECT 
        CustomerID,
        MIN(OrderDate) AS FirstOrderDate
    FROM OrderInfo
    GROUP BY CustomerID
    HAVING COUNT(*) > 1
) AS first_orders ON Customer.CustomerID = first_orders.CustomerID
WHERE OrderInfo.OrderDate = first_orders.FirstOrderDate
    AND OrderInfo.OrderID = (
        SELECT MIN(OrderID)
        FROM OrderInfo AS o2
        WHERE o2.CustomerID = Customer.CustomerID
            AND o2.OrderDate = first_orders.FirstOrderDate
    )
ORDER BY Customer.CustomerName;
