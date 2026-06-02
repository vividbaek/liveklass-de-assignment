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
