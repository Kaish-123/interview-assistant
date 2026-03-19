-- Percentage of vegetarian-only restaurants (expected: 1.03)
-- "Vegetarian-only" = all items vegetarian AND at least one item is veg (not vegan).
-- So we exclude: (1) any non-veg item, (2) all-vegan restaurants.

SELECT ROUND(
    (SELECT COUNT(DISTINCT m.id)
     FROM merchants m
     JOIN menus me ON m.id = me.merchant_id
     JOIN items i ON me.id = i.menu_id
     WHERE i.is_vegetarian_flg = 1
       AND i.is_vegan_flg = 0
       AND NOT EXISTS (
           SELECT 1
           FROM menus me2
           JOIN items i2 ON me2.id = i2.menu_id
           WHERE me2.merchant_id = m.id
             AND i2.is_vegetarian_flg = 0
       )
    ) * 100.0 / (SELECT COUNT(DISTINCT id) FROM merchants),
    2
) AS perc_veg_only_res;
