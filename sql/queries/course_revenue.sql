SELECT
    course_id,
    COUNT(*) AS purchase_count,
    COALESCE(SUM(amount), 0) AS total_revenue
FROM events
WHERE event_type = 'purchase_completed'
GROUP BY course_id
ORDER BY total_revenue DESC;