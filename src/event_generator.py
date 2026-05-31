from __future__ import annotations

import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4


Event = dict[str, Any]

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

COURSES = [
    {
        "course_id": "course_ontology_basic",
        "price": Decimal("59000.00"),
        "lessons": [
            "lesson_ontology_intro",
            "lesson_knowledge_graph_01",
            "lesson_rdf_basic",
        ],
    },
    {
        "course_id": "course_data_pipeline",
        "price": Decimal("79000.00"),
        "lessons": [
            "lesson_pipeline_intro",
            "lesson_batch_processing",
            "lesson_pipeline_monitoring",
        ],
    },
    {
        "course_id": "course_ai_writing",
        "price": Decimal("49000.00"),
        "lessons": [
            "lesson_prompt_intro",
            "lesson_content_workflow",
            "lesson_ai_review",
        ],
    },
    {
        "course_id": "course_marketing_growth",
        "price": Decimal("69000.00"),
        "lessons": [
            "lesson_growth_funnel",
            "lesson_content_marketing",
            "lesson_conversion_analysis",
        ],
    },
    {
        "course_id": "course_live_commerce",
        "price": Decimal("89000.00"),
        "lessons": [
            "lesson_live_setup",
            "lesson_sales_script",
            "lesson_live_qa",
        ],
    },
]

DEVICE_TYPES = ["desktop", "mobile", "tablet"]
PAYMENT_METHODS = ["card", "kakao_pay", "bank_transfer", "toss_pay"]
ERRORS = [
    ("payment", "PAYMENT_FAILED"),
    ("video", "VIDEO_BUFFERING"),
    ("live_class", "LIVE_JOIN_TIMEOUT"),
    ("lesson", "LESSON_LOAD_FAILED"),
]


def generate_events(target_count: int = 1000, seed: int | None = 42) -> list[Event]:
    rng = random.Random(seed)
    events: list[Event] = []

    while len(events) < target_count:
        events.extend(_generate_session_events(rng))

    return events[:target_count]


def _generate_session_events(rng: random.Random) -> list[Event]:
    session_id = f"sess_{uuid4().hex[:12]}"
    base_time = _random_event_time(rng)
    device_type = rng.choice(DEVICE_TYPES)
    course = rng.choice(COURSES)
    course_id = course["course_id"]
    lesson_id = rng.choice(course["lessons"])

    is_member = rng.random() < 0.45
    user_id = _new_user_id() if is_member else None
    user_type = "member" if is_member else "guest"

    session_events: list[Event] = []
    page_url = rng.choice(["/", "/courses", "/webinars", "/community"])
    session_events.append(
        _base_event(
            event_type="page_view",
            event_time=base_time,
            session_id=session_id,
            user_id=user_id,
            user_type=user_type,
            device_type=device_type,
            page_url=page_url,
            duration_seconds=rng.randint(8, 90),
        )
    )

    if rng.random() > 0.88:
        return session_events

    course_view_duration = rng.randint(20, 260)
    session_events.append(
        _base_event(
            event_type="course_view",
            event_time=base_time + timedelta(seconds=rng.randint(10, 90)),
            session_id=session_id,
            user_id=user_id,
            user_type=user_type,
            device_type=device_type,
            course_id=course_id,
            page_url=f"/courses/{course_id}",
            duration_seconds=course_view_duration,
        )
    )

    preview_watch_seconds = 0
    watched_lesson = rng.random() < 0.72
    if watched_lesson:
        lesson_access_type = _choose_lesson_access_type(rng, user_type)
        preview_watch_seconds = _watch_seconds(rng, lesson_access_type)
        session_events.append(
            _base_event(
                event_type="lesson_started",
                event_time=base_time + timedelta(seconds=rng.randint(90, 240)),
                session_id=session_id,
                user_id=user_id,
                user_type=user_type,
                device_type=device_type,
                course_id=course_id,
                lesson_id=lesson_id,
                lesson_access_type=lesson_access_type,
                page_url=f"/courses/{course_id}/lessons/{lesson_id}",
                duration_seconds=preview_watch_seconds,
            )
        )

        if preview_watch_seconds >= 240 or rng.random() < 0.35:
            session_events.append(
                _base_event(
                    event_type="lesson_completed",
                    event_time=base_time + timedelta(seconds=rng.randint(300, 900)),
                    session_id=session_id,
                    user_id=user_id,
                    user_type=user_type,
                    device_type=device_type,
                    course_id=course_id,
                    lesson_id=lesson_id,
                    lesson_access_type=lesson_access_type,
                    page_url=f"/courses/{course_id}/lessons/{lesson_id}",
                    duration_seconds=max(preview_watch_seconds, rng.randint(300, 1200)),
                )
            )

    purchase_probability = _purchase_probability(
        course_view_duration=course_view_duration,
        watch_seconds=preview_watch_seconds,
        is_member=is_member,
    )
    started_checkout = rng.random() < min(purchase_probability + 0.18, 0.72)

    if started_checkout:
        if user_id is None:
            user_id = _new_user_id()
        user_type = "member"
        session_events.append(
            _base_event(
                event_type="checkout_started",
                event_time=base_time + timedelta(seconds=rng.randint(600, 1300)),
                session_id=session_id,
                user_id=user_id,
                user_type=user_type,
                device_type=device_type,
                course_id=course_id,
                page_url=f"/checkout/{course_id}",
            )
        )

        if rng.random() < purchase_probability:
            session_events.append(
                _base_event(
                    event_type="purchase_completed",
                    event_time=base_time + timedelta(seconds=rng.randint(900, 1700)),
                    session_id=session_id,
                    user_id=user_id,
                    user_type=user_type,
                    device_type=device_type,
                    course_id=course_id,
                    page_url="/checkout/success",
                    amount=course["price"],
                    payment_method=rng.choice(PAYMENT_METHODS),
                )
            )

    if rng.random() < 0.08:
        error_area, error_code = rng.choice(ERRORS)
        session_events.append(
            _base_event(
                event_type="error_occurred",
                event_time=base_time + timedelta(seconds=rng.randint(60, 1600)),
                session_id=session_id,
                user_id=user_id,
                user_type=user_type,
                device_type=device_type,
                course_id=course_id,
                lesson_id=lesson_id if error_area in {"video", "live_class", "lesson"} else None,
                lesson_access_type=None,
                page_url=_error_page_url(error_area, course_id, lesson_id),
                error_area=error_area,
                error_code=error_code,
            )
        )

    return sorted(session_events, key=lambda event: event["event_time"])


def _base_event(
    *,
    event_type: str,
    event_time: datetime,
    session_id: str,
    user_id: str | None,
    user_type: str,
    device_type: str,
    course_id: str | None = None,
    lesson_id: str | None = None,
    lesson_access_type: str | None = None,
    page_url: str | None = None,
    duration_seconds: int | None = None,
    amount: Decimal | None = None,
    payment_method: str | None = None,
    error_area: str | None = None,
    error_code: str | None = None,
) -> Event:
    return {
        "event_id": str(uuid4()),
        "event_type": event_type,
        "event_time": event_time,
        "user_id": user_id,
        "session_id": session_id,
        "user_type": user_type,
        "course_id": course_id,
        "lesson_id": lesson_id,
        "lesson_access_type": lesson_access_type,
        "page_url": page_url,
        "device_type": device_type,
        "duration_seconds": duration_seconds,
        "amount": amount,
        "payment_method": payment_method,
        "error_area": error_area,
        "error_code": error_code,
    }


def _random_event_time(rng: random.Random) -> datetime:
    now = datetime.now().replace(microsecond=0)
    return now - timedelta(
        days=rng.randint(0, 6),
        hours=rng.randint(0, 23),
        minutes=rng.randint(0, 59),
        seconds=rng.randint(0, 59),
    )


def _new_user_id() -> str:
    return f"user_{uuid4().hex[:10]}"


def _choose_lesson_access_type(rng: random.Random, user_type: str) -> str:
    if user_type == "guest":
        return "free_preview"
    return "free_preview" if rng.random() < 0.35 else "paid_enrolled"


def _watch_seconds(rng: random.Random, lesson_access_type: str) -> int:
    if lesson_access_type == "free_preview":
        return rng.randint(30, 600)
    return rng.randint(180, 1800)


def _purchase_probability(
    *, course_view_duration: int, watch_seconds: int, is_member: bool
) -> float:
    probability = 0.08

    if course_view_duration >= 90:
        probability += 0.08
    if course_view_duration >= 180:
        probability += 0.08
    if watch_seconds >= 180:
        probability += 0.08
    if watch_seconds >= 300:
        probability += 0.12
    if is_member:
        probability += 0.08

    return min(probability, 0.62)


def _error_page_url(error_area: str, course_id: str, lesson_id: str) -> str:
    if error_area == "payment":
        return f"/checkout/{course_id}"
    if error_area == "live_class":
        return f"/live/{course_id}/{lesson_id}"
    return f"/courses/{course_id}/lessons/{lesson_id}"
