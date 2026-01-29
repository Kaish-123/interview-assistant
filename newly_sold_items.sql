/* 
SQL - RK - 3.1 Number of new items sold between March 23, 2021 and April 1, 2021

Description: Create a query to determine the count of newly sold items over the past 10 days starting from April 1, 2021.
Newly sold items are defined as items that have been sold for the first time in the entire sales history.
*/

-- Solution: Count items sold in the date range that have never been sold before
SELECT 
    COUNT(DISTINCT oi.item_id) AS count_of_new_items
FROM 
    order_items oi
INNER JOIN 
    orders o ON oi.order_id = o.id
WHERE 
    o.order_date BETWEEN '2021-03-23' AND '2021-04-01'
    AND NOT EXISTS (
        -- Check if this item was sold before March 23, 2021
        SELECT 1
        FROM order_items oi2
        INNER JOIN orders o2 ON oi2.order_id = o2.id
        WHERE oi2.item_id = oi.item_id
        AND o2.order_date < '2021-03-23'
    );

-- Alternative solution using window functions (more efficient for large datasets)
SELECT 
    COUNT(DISTINCT item_id) AS count_of_new_items
FROM (
    SELECT 
        oi.item_id,
        o.order_date,
        MIN(o.order_date) OVER (PARTITION BY oi.item_id) AS first_sale_date
    FROM 
        order_items oi
    INNER JOIN 
        orders o ON oi.order_id = o.id
    WHERE 
        o.order_date <= '2021-04-01'
) AS item_sales
WHERE 
    order_date BETWEEN '2021-03-23' AND '2021-04-01'
    AND first_sale_date >= '2021-03-23';

-- Alternative using subquery with MIN aggregation
SELECT 
    COUNT(DISTINCT oi.item_id) AS count_of_new_items
FROM 
    order_items oi
INNER JOIN 
    orders o ON oi.order_id = o.id
WHERE 
    o.order_date BETWEEN '2021-03-23' AND '2021-04-01'
    AND oi.item_id IN (
        -- Items whose first sale date is in our target range
        SELECT 
            oi2.item_id
        FROM 
            order_items oi2
        INNER JOIN 
            orders o2 ON oi2.order_id = o2.id
        GROUP BY 
            oi2.item_id
        HAVING 
            MIN(o2.order_date) BETWEEN '2021-03-23' AND '2021-04-01'
    );
