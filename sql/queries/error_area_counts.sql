SELECT error_area, COUNT(*) AS error_count
FROM events
WHERE event_type = 'error_occurred'
GROUP BY error_area
ORDER BY error_count DESC;

