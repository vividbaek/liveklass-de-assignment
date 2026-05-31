CREATE TABLE IF NOT EXISTS events (
    -- 이벤트 한 건을 구분하는 고유 ID입니다.
    event_id UUID PRIMARY KEY,

    -- 이벤트 종류입니다.
    -- 예: page_view, course_view, lesson_started, lesson_completed, checkout_started, purchase_completed, error_occurred
    event_type VARCHAR(50) NOT NULL,

    -- 이벤트가 실제로 발생한 시간입니다.
    event_time TIMESTAMP NOT NULL,

    -- 로그인 회원이면 user_id를 저장하고, 비회원이면 NULL로 둡니다.
    user_id VARCHAR(50),

    -- 로그인 여부와 관계없이 방문 단위를 추적하기 위한 세션 ID입니다.
    session_id VARCHAR(50) NOT NULL,

    -- 사용자가 회원인지 비회원인지 구분합니다.
    -- 예: guest, member
    user_type VARCHAR(20) NOT NULL,

    -- 강의 전체를 구분하기 위한 ID입니다.
    -- 예: course_ontology_basic
    course_id VARCHAR(50),

    -- 강의 안의 개별 콘텐츠를 구분하기 위한 ID입니다.
    -- 예: lesson_knowledge_graph_01
    lesson_id VARCHAR(50),

    -- 무료 체험 콘텐츠인지 유료 수강 콘텐츠인지 구분합니다.
    -- 예: free_preview, paid_enrolled
    lesson_access_type VARCHAR(30),

    -- 이벤트가 발생한 페이지 경로입니다.
    -- 예: /courses, /checkout/success
    page_url TEXT,

    -- 사용자가 접근한 기기 유형입니다.
    -- 예: desktop, mobile, tablet
    device_type VARCHAR(20),

    -- 페이지 체류 시간 또는 강의 콘텐츠 시청 시간을 초 단위로 저장합니다.
    -- page_view/course_view에서는 페이지 체류 시간, lesson_started/lesson_completed에서는 시청 시간으로 사용합니다.
    duration_seconds INTEGER,

    -- 결제 완료 이벤트에서 결제 금액을 저장합니다.
    amount NUMERIC(10, 2),

    -- 결제 완료 이벤트에서 결제 수단을 저장합니다.
    -- 예: card, kakao_pay, bank_transfer
    payment_method VARCHAR(30),

    -- 오류가 발생한 영역입니다.
    -- 예: payment, video, live_class, lesson
    error_area VARCHAR(30),

    -- 오류 유형을 구분하기 위한 코드입니다.
    -- 예: PAYMENT_FAILED, VIDEO_BUFFERING, LIVE_JOIN_TIMEOUT
    error_code VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_events_event_type
ON events (event_type);

CREATE INDEX IF NOT EXISTS idx_events_event_time
ON events (event_time);

CREATE INDEX IF NOT EXISTS idx_events_course_id
ON events (course_id);

CREATE INDEX IF NOT EXISTS idx_events_user_id
ON events (user_id);
