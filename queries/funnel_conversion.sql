SELECT
    user_segment,
    COUNT(DISTINCT CASE WHEN event_type = 'page_view' THEN user_id END) AS page_view_users,
    COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart' THEN user_id END) AS add_to_cart_users,
    COUNT(DISTINCT CASE WHEN event_type = 'checkout' THEN user_id END) AS checkout_users,
    COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END) AS purchase_users,
    ROUND(
        100.0
        * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END)
        / NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'page_view' THEN user_id END), 0),
        2
    ) AS conversion_rate
FROM events
GROUP BY user_segment
ORDER BY conversion_rate DESC;
