\echo '1. 이벤트 타입별 발생 수'
SELECT
    event_type,
    COUNT(*) AS event_count
FROM events
GROUP BY event_type
ORDER BY event_count DESC;

\echo ''
\echo '2. 강의별 매출'
SELECT
    course_id,
    COUNT(*) AS purchase_count,
    SUM(amount) AS total_revenue
FROM events
WHERE event_type = 'purchase_completed'
GROUP BY course_id
ORDER BY total_revenue DESC;

\echo ''
\echo '3. checkout_started -> purchase_completed 전환율'
WITH checkout_sessions AS (
    SELECT DISTINCT session_id
    FROM events
    WHERE event_type = 'checkout_started'
),
purchase_sessions AS (
    SELECT DISTINCT session_id
    FROM events
    WHERE event_type = 'purchase_completed'
)
SELECT
    COUNT(*) AS checkout_sessions,
    COUNT(p.session_id) AS purchased_sessions,
    ROUND(
        COUNT(p.session_id)::numeric / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS conversion_rate_percent
FROM checkout_sessions c
LEFT JOIN purchase_sessions p
    ON c.session_id = p.session_id;

\echo ''
\echo '4. 무료 체험 300초 이상 시청 session의 구매 전환율'
WITH preview_sessions AS (
    SELECT DISTINCT session_id
    FROM events
    WHERE event_type = 'lesson_started'
      AND lesson_access_type = 'free_preview'
      AND duration_seconds >= 300
),
purchase_sessions AS (
    SELECT DISTINCT session_id
    FROM events
    WHERE event_type = 'purchase_completed'
)
SELECT
    COUNT(*) AS preview_300_sessions,
    COUNT(p.session_id) AS purchased_sessions,
    ROUND(
        COUNT(p.session_id)::numeric / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS conversion_rate_percent
FROM preview_sessions ps
LEFT JOIN purchase_sessions p
    ON ps.session_id = p.session_id;

\echo ''
\echo '5. 오류 영역별 발생 수'
SELECT
    error_area,
    COUNT(*) AS error_count
FROM events
WHERE event_type = 'error_occurred'
GROUP BY error_area
ORDER BY error_count DESC;
