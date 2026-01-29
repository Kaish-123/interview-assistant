/* 
SQL - RK - 2.1 Order details of dashers with multiple orders

Description: Write a SQL query to find the order details for dashers who handled multiple orders on January 1st, 2021.

Bonus: Can you write the query without using joins?
*/

-- Solution with JOINs
SELECT 
    o.id AS order_id,
    o.consumer_id,
    o.merchant_id,
    o.dasher_id,
    d.name AS dasher_name,
    o.address_id,
    o.order_time,
    o.order_date,
    o.status,
    o.is_pickup_flg,
    o.rating,
    o.subtotal,
    o.fees,
    o.tax,
    o.tip,
    o.total
FROM 
    orders o
INNER JOIN 
    dashers d ON o.dasher_id = d.id
INNER JOIN (
    SELECT 
        dasher_id
    FROM 
        orders
    WHERE 
        order_date = '2021-01-01'
    GROUP BY 
        dasher_id
    HAVING 
        COUNT(*) > 1
) multi_order_dashers ON o.dasher_id = multi_order_dashers.dasher_id
WHERE 
    o.order_date = '2021-01-01'
ORDER BY 
    o.dasher_id, o.order_time;

-- Bonus: Solution without JOINs (using subqueries)
SELECT 
    o.id AS order_id,
    o.consumer_id,
    o.merchant_id,
    o.dasher_id,
    (SELECT d.name FROM dashers d WHERE d.id = o.dasher_id) AS dasher_name,
    o.address_id,
    o.order_time,
    o.order_date,
    o.status,
    o.is_pickup_flg,
    o.rating,
    o.subtotal,
    o.fees,
    o.tax,
    o.tip,
    o.total
FROM 
    orders o
WHERE 
    o.order_date = '2021-01-01'
    AND o.dasher_id IN (
        SELECT 
            dasher_id
        FROM 
            orders
        WHERE 
            order_date = '2021-01-01'
        GROUP BY 
            dasher_id
        HAVING 
            COUNT(*) > 1
    )
ORDER BY 
    o.dasher_id, o.order_time;

-- Simplest solution without JOINs (SELECT *)
SELECT *
FROM orders
WHERE dasher_id IN (
    SELECT dasher_id
    FROM orders
    WHERE order_date = '2021-01-01'
    GROUP BY dasher_id
    HAVING COUNT(id) > 1
)
AND order_date = '2021-01-01';
