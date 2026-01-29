/* 
SQL - RK - 2.2 Merchant names with no menu de-activation

Description: Create a query to retrieve the list of merchants, ordered alphabetically by their name, 
who have never deactivated any of their menus.
*/

-- Solution: Merchants who have never deactivated any menu
-- (i.e., no menus with is_active_flg = 0, or merchants with no menus at all)
SELECT 
    m.id,
    m.name
FROM 
    merchants m
WHERE 
    m.id NOT IN (
        SELECT DISTINCT merchant_id
        FROM menus
        WHERE is_active_flg = 0
    )
ORDER BY 
    m.name;

-- Alternative solution using LEFT JOIN and GROUP BY
SELECT 
    m.id,
    m.name
FROM 
    merchants m
LEFT JOIN 
    menus mn ON m.id = mn.merchant_id AND mn.is_active_flg = 0
WHERE 
    mn.merchant_id IS NULL
GROUP BY 
    m.id, m.name
ORDER BY 
    m.name;

-- Alternative using NOT EXISTS (often more efficient)
SELECT 
    m.id,
    m.name
FROM 
    merchants m
WHERE 
    NOT EXISTS (
        SELECT 1
        FROM menus
        WHERE merchant_id = m.id 
        AND is_active_flg = 0
    )
ORDER BY 
    m.name;
