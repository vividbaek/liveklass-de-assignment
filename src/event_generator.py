from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from src.enums.event_values import (
    COURSES,
    DEVICE_TYPES,
    ERRORS,
    PAYMENT_METHODS,
    SESSION_SCENARIOS,
)


Event = dict[str, Any]
DEFAULT_BASE_TIME = datetime(2026, 1, 1, 12, 0, 0)


def generate_events(
    target_sessions: int = 250,
    seed: int | None = 42,
    *,
    approx_target_count: int | None = None,
    base_time: datetime | None = None,
) -> list[Event]:
    rng = random.Random(seed)
    session_count = (
        max(1, approx_target_count // 4)
        if approx_target_count is not None
        else target_sessions
    )
    reference_time = base_time or DEFAULT_BASE_TIME
    events: list[Event] = []

    for _ in range(session_count):
        events.extend(_generate_session_events(rng, reference_time))

    return sorted(events, key=lambda event: event["event_time"])


def _generate_session_events(
    rng: random.Random,
    reference_time: datetime,
) -> list[Event]:
    session_id = _new_compact_id("sess", rng, 12)
    base_time = _random_session_start_time(rng, reference_time)
    device_type = rng.choice(DEVICE_TYPES)
    course = rng.choice(COURSES)
    lesson = rng.choice(course["lessons"])
    scenario = _choose_scenario(rng)

    is_member = scenario == "paid_learning" or rng.random() < 0.42
    user_id = _new_user_id(rng) if is_member else None
    user_type = "member" if is_member else "guest"

    context = {
        "session_id": session_id,
        "user_id": user_id,
        "user_type": user_type,
        "device_type": device_type,
        "course_id": course["course_id"],
        "lesson_id": lesson["lesson_id"],
    }

    cursor = base_time
    events: list[Event] = []

    page_duration = rng.randint(15, 90)
    events.append(
        _base_event(
            event_type="page_view",
            rng=rng,
            event_time=cursor,
            page_url=rng.choice(["/", "/courses", "/webinars", "/community"]),
            duration_seconds=page_duration,
            **_event_context(context, course_id=None, lesson_id=None),
        )
    )
    cursor = _move_time(cursor, page_duration, rng.randint(5, 30))

    course_duration = _course_view_duration(rng, scenario)
    events.append(
        _base_event(
            event_type="course_view",
            rng=rng,
            event_time=cursor,
            page_url=f"/courses/{course['course_id']}",
            duration_seconds=course_duration,
            **_event_context(context, lesson_id=None),
        )
    )
    cursor = _move_time(cursor, course_duration, rng.randint(10, 60))

    if scenario == "browse_only":
        return events

    lesson_access_type = (
        "paid_enrolled" if scenario == "paid_learning" else "free_preview"
    )
    watch_seconds = _watch_seconds(rng, scenario)
    events.append(
        _base_event(
            event_type="lesson_started",
            rng=rng,
            event_time=cursor,
            lesson_access_type=lesson_access_type,
            page_url=f"/courses/{course['course_id']}/lessons/{lesson['lesson_id']}",
            duration_seconds=watch_seconds,
            **context,
        )
    )
    cursor = _move_time(cursor, watch_seconds, rng.randint(10, 90))

    if scenario in {
        "preview_completed_no_purchase",
        "preview_to_purchase",
        "paid_learning",
    }:
        completed_seconds = max(watch_seconds, _completed_watch_seconds(rng, scenario))
        events.append(
            _base_event(
                event_type="lesson_completed",
                rng=rng,
                event_time=cursor,
                lesson_access_type=lesson_access_type,
                page_url=(
                    f"/courses/{course['course_id']}/lessons/{lesson['lesson_id']}"
                ),
                duration_seconds=completed_seconds,
                **context,
            )
        )
        cursor = _move_time(cursor, rng.randint(20, 90), rng.randint(20, 120))

    if scenario in {
        "checkout_abandoned",
        "preview_to_purchase",
        "payment_error",
    }:
        if context["user_id"] is None:
            context["user_id"] = _new_user_id(rng)
            context["user_type"] = "member"

        events.append(
            _base_event(
                event_type="checkout_started",
                rng=rng,
                event_time=cursor,
                page_url=f"/checkout/{course['course_id']}",
                **_event_context(context, lesson_id=None),
            )
        )
        cursor = _move_time(cursor, rng.randint(30, 120), rng.randint(10, 60))

    if scenario == "payment_error":
        events.append(
            _base_event(
                event_type="error_occurred",
                rng=rng,
                event_time=cursor,
                page_url=f"/checkout/{course['course_id']}",
                error_area="payment",
                error_code="PAYMENT_FAILED",
                **_event_context(context, lesson_id=None),
            )
        )
        return events

    if scenario in {"preview_to_purchase", "paid_learning"}:
        if context["user_id"] is None:
            context["user_id"] = _new_user_id(rng)
            context["user_type"] = "member"

        if scenario == "paid_learning" and not _has_event(events, "checkout_started"):
            events.append(
                _base_event(
                    event_type="checkout_started",
                    rng=rng,
                    event_time=cursor,
                    page_url=f"/checkout/{course['course_id']}",
                    **_event_context(context, lesson_id=None),
                )
            )
            cursor = _move_time(cursor, rng.randint(30, 120), rng.randint(10, 60))

        events.append(
            _base_event(
                event_type="purchase_completed",
                rng=rng,
                event_time=cursor,
                page_url="/checkout/success",
                amount=course["price"],
                payment_method=rng.choice(PAYMENT_METHODS),
                **_event_context(context, lesson_id=None),
            )
        )

    if rng.random() < 0.06:
        error_area, error_code = rng.choice(
            [error for error in ERRORS if error[0] != "payment"]
        )
        events.append(
            _base_event(
                event_type="error_occurred",
                rng=rng,
                event_time=cursor + timedelta(seconds=rng.randint(30, 300)),
                page_url=_error_page_url(
                    error_area,
                    course["course_id"],
                    lesson["lesson_id"],
                ),
                error_area=error_area,
                error_code=error_code,
                **context,
            )
        )

    return events


def _base_event(
    *,
    event_type: str,
    rng: random.Random,
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
    amount: int | None = None,
    payment_method: str | None = None,
    error_area: str | None = None,
    error_code: str | None = None,
) -> Event:
    return {
        "event_id": _new_uuid(rng),
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


def _event_context(context: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    return {**context, **overrides}


def _choose_scenario(rng: random.Random) -> str:
    scenarios = [scenario for scenario, _ in SESSION_SCENARIOS]
    weights = [weight for _, weight in SESSION_SCENARIOS]
    return rng.choices(scenarios, weights=weights, k=1)[0]


def _random_session_start_time(
    rng: random.Random,
    reference_time: datetime,
) -> datetime:
    return reference_time.replace(microsecond=0) - timedelta(
        days=rng.randint(0, 6),
        hours=rng.randint(0, 23),
        minutes=rng.randint(0, 59),
        seconds=rng.randint(0, 59),
    )


def _move_time(
    event_time: datetime,
    duration_seconds: int,
    gap_seconds: int,
) -> datetime:
    return event_time + timedelta(seconds=duration_seconds + gap_seconds)


def _new_user_id(rng: random.Random) -> str:
    return _new_compact_id("user", rng, 10)


def _new_compact_id(prefix: str, rng: random.Random, length: int) -> str:
    return f"{prefix}_{rng.getrandbits(length * 4):0{length}x}"


def _new_uuid(rng: random.Random) -> str:
    return str(UUID(int=rng.getrandbits(128), version=4))


def _course_view_duration(rng: random.Random, scenario: str) -> int:
    if scenario in {"preview_to_purchase", "paid_learning"}:
        return rng.randint(120, 360)
    if scenario in {"checkout_abandoned", "payment_error"}:
        return rng.randint(80, 240)
    if scenario == "browse_only":
        return rng.randint(15, 100)
    return rng.randint(45, 220)


def _watch_seconds(rng: random.Random, scenario: str) -> int:
    if scenario == "preview_to_purchase":
        return rng.randint(120, 900)
    if scenario == "preview_completed_no_purchase":
        return rng.randint(300, 900)
    if scenario == "paid_learning":
        return rng.randint(600, 1800)
    if scenario == "checkout_abandoned":
        return rng.randint(120, 600)
    return rng.randint(20, 240)


def _completed_watch_seconds(rng: random.Random, scenario: str) -> int:
    if scenario == "paid_learning":
        return rng.randint(900, 2400)
    return rng.randint(360, 1200)


def _has_event(events: list[Event], event_type: str) -> bool:
    return any(event["event_type"] == event_type for event in events)


def _error_page_url(error_area: str, course_id: str, lesson_id: str) -> str:
    if error_area == "live_class":
        return f"/live/{course_id}/{lesson_id}"
    return f"/courses/{course_id}/lessons/{lesson_id}"
