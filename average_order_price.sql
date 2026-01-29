/* 
SQL - RK - 1.2 Average order price

Description: List the days and their average order price where the average order price 
rounded to the whole number is greater than 60. Order the results by order_date.

FREE HINT: Order Price is total
*/

SELECT 
    order_date,
    ROUND(AVG(total)) AS avg_order_price
FROM 
    orders
GROUP BY 
    order_date
HAVING 
    ROUND(AVG(total)) > 60
ORDER BY 
    order_date;
