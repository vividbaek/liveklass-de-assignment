from __future__ import annotations

from typing import TypedDict


class Lesson(TypedDict):
    lesson_id: str
    lesson_name: str


class Course(TypedDict):
    course_id: str
    course_name: str
    price: int
    lessons: list[Lesson]


EVENT_COLUMNS = [
    "event_id",
    "event_type",
    "event_time",
    "user_id",
    "session_id",
    "user_type",
    "course_id",
    "lesson_id",
    "lesson_access_type",
    "page_url",
    "device_type",
    "duration_seconds",
    "amount",
    "payment_method",
    "error_area",
    "error_code",
]

COURSES: list[Course] = [
    {
        "course_id": "course_class_setup",
        "course_name": "[첫 시작하기] 클래스 세팅하기",
        "price": 59000,
        "lessons": [
            {
                "lesson_id": "lesson_admin_intro",
                "lesson_name": "관리자 페이지 둘러보기",
            },
            {
                "lesson_id": "lesson_curriculum_setup",
                "lesson_name": "커리큘럼 구성하기",
            },
            {
                "lesson_id": "lesson_payment_setup",
                "lesson_name": "결제와 수강 신청 설정",
            },
        ],
    },
    {
        "course_id": "course_zoom_basic",
        "course_name": "[첫 시작하기] 초보를 위한 Zoom 사용법",
        "price": 79000,
        "lessons": [
            {
                "lesson_id": "lesson_zoom_intro",
                "lesson_name": "Zoom 수업 환경 준비",
            },
            {
                "lesson_id": "lesson_live_open",
                "lesson_name": "실시간 강의 개설하기",
            },
            {
                "lesson_id": "lesson_live_operation",
                "lesson_name": "라이브 수업 운영 체크리스트",
            },
        ],
    },
    {
        "course_id": "course_liveklass_atoz",
        "course_name": "[첫 시작하기] 라이브클래스의 효과적인 활용을 위한 A to Z",
        "price": 49000,
        "lessons": [
            {
                "lesson_id": "lesson_site_builder",
                "lesson_name": "강의 홈페이지 만들기",
            },
            {
                "lesson_id": "lesson_student_crm",
                "lesson_name": "수강생 관리와 CRM",
            },
            {
                "lesson_id": "lesson_progress_report",
                "lesson_name": "진도율과 학습 데이터 확인",
            },
        ],
    },
    {
        "course_id": "course_content_monetization",
        "course_name": "[첫 시작하기] 내 콘텐츠로 수익 창출하기",
        "price": 69000,
        "lessons": [
            {
                "lesson_id": "lesson_product_design",
                "lesson_name": "지식 상품 설계하기",
            },
            {
                "lesson_id": "lesson_sales_page",
                "lesson_name": "판매 페이지 구성하기",
            },
            {
                "lesson_id": "lesson_conversion_metric",
                "lesson_name": "결제 전환 지표 읽기",
            },
        ],
    },
    {
        "course_id": "course_content_planning",
        "course_name": "[첫 시작하기] 콘텐츠 기획 방법",
        "price": 89000,
        "lessons": [
            {
                "lesson_id": "lesson_target_student",
                "lesson_name": "타깃 수강생 정의하기",
            },
            {
                "lesson_id": "lesson_curriculum_planning",
                "lesson_name": "커리큘럼 흐름 설계",
            },
            {
                "lesson_id": "lesson_content_production",
                "lesson_name": "콘텐츠 제작 일정 만들기",
            },
        ],
    },
]

COURSE_LABELS = {
    course["course_id"]: course["course_name"]
    for course in COURSES
}

LESSON_LABELS = {
    lesson["lesson_id"]: lesson["lesson_name"]
    for course in COURSES
    for lesson in course["lessons"]
}

DEVICE_TYPES = ["desktop", "mobile", "tablet"]

PAYMENT_METHODS = ["card", "kakao_pay", "bank_transfer", "toss_pay"]

ERRORS = [
    ("payment", "PAYMENT_FAILED"),
    ("video", "VIDEO_BUFFERING"),
    ("live_class", "LIVE_JOIN_TIMEOUT"),
    ("lesson", "LESSON_LOAD_FAILED"),
]

SESSION_SCENARIOS = [
    ("browse_only", 0.18),
    ("preview_dropoff", 0.18),
    ("preview_completed_no_purchase", 0.20),
    ("checkout_abandoned", 0.14),
    ("preview_to_purchase", 0.18),
    ("payment_error", 0.07),
    ("paid_learning", 0.05),
]
