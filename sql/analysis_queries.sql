\echo '1. Session funnel conversion'
WITH session_steps AS (
    SELECT
        session_id,
        BOOL_OR(event_type = 'course_view') AS viewed_course,
        BOOL_OR(event_type = 'lesson_started') AS started_lesson,
        BOOL_OR(event_type = 'checkout_started') AS started_checkout,
        BOOL_OR(event_type = 'purchase_completed') AS completed_purchase
    FROM events
    GROUP BY session_id
),
funnel AS (
    SELECT 1 AS step_order, 'course_view' AS step_name, COUNT(*) AS session_count
    FROM session_steps
    WHERE viewed_course

    UNION ALL

    SELECT 2, 'lesson_started', COUNT(*)
    FROM session_steps
    WHERE started_lesson

    UNION ALL

    SELECT 3, 'checkout_started', COUNT(*)
    FROM session_steps
    WHERE started_checkout

    UNION ALL

    SELECT 4, 'purchase_completed', COUNT(*)
    FROM session_steps
    WHERE completed_purchase
)
SELECT
    step_name,
    session_count,
    ROUND(
        session_count::numeric
        / NULLIF(FIRST_VALUE(session_count) OVER (ORDER BY step_order), 0) * 100,
        2
    ) AS conversion_from_course_view_percent,
    ROUND(
        session_count::numeric
        / NULLIF(LAG(session_count) OVER (ORDER BY step_order), 0) * 100,
        2
    ) AS conversion_from_previous_step_percent
FROM funnel
ORDER BY step_order;

\echo ''
\echo '2. Free preview watch duration bucket conversion'
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

\echo ''
\echo '3. Course revenue and purchase count'
SELECT
    course_id,
    COUNT(*) AS purchase_count,
    COALESCE(SUM(amount), 0) AS total_revenue
FROM events
WHERE event_type = 'purchase_completed'
GROUP BY course_id
ORDER BY total_revenue DESC;

\echo ''
\echo '4. Error count by area'
SELECT
    error_area,
    COUNT(*) AS error_count
FROM events
WHERE event_type = 'error_occurred'
GROUP BY error_area
ORDER BY error_count DESC;
