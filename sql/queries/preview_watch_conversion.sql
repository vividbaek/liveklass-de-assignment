WITH preview_sessions AS (
    SELECT
        session_id,
        CASE
            WHEN duration_seconds < 60 THEN '0-60s'
            WHEN duration_seconds < 180 THEN '60-180s'
            WHEN duration_seconds < 300 THEN '180-300s'
            ELSE '300s+'
        END AS watch_bucket,
        CASE
            WHEN duration_seconds < 60 THEN 1
            WHEN duration_seconds < 180 THEN 2
            WHEN duration_seconds < 300 THEN 3
            ELSE 4
        END AS bucket_order
    FROM events
    WHERE event_type = 'lesson_started'
      AND lesson_access_type = 'free_preview'
),
purchase_sessions AS (
    SELECT DISTINCT session_id
    FROM events
    WHERE event_type = 'purchase_completed'
)
SELECT
    p.watch_bucket,
    COUNT(*) AS preview_sessions,
    COUNT(ps.session_id) AS purchased_sessions,
    ROUND(
        COUNT(ps.session_id)::numeric / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS conversion_rate_percent
FROM preview_sessions p
LEFT JOIN purchase_sessions ps
    ON p.session_id = ps.session_id
GROUP BY p.bucket_order, p.watch_bucket
ORDER BY p.bucket_order;
