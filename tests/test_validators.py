from src.events.validators import validate_event_keys
from src.enums.event_values import EVENT_COLUMNS
from datetime import datetime


def make_event():
    # EVENT_COLUMNS와 일치하는 최소 유효 이벤트를 구성합니다.
    now = datetime.now()
    sample = {
        "event_id": "00000000-0000-0000-0000-000000000000",
        "event_type": "page_view",
        "event_time": now,
        "user_id": None,
        "session_id": "sess_test",
        "user_type": "guest",
        "course_id": None,
        "lesson_id": None,
        "lesson_access_type": None,
        "page_url": "/",
        "device_type": "desktop",
        "duration_seconds": 10,
        "amount": None,
        "payment_method": None,
        "error_area": None,
        "error_code": None,
    }
    return sample


def test_validate_event_keys_ok():
    ev = make_event()
    validate_event_keys([ev])


def test_validate_event_keys_missing():
    ev = make_event()
    ev.pop("event_type")
    try:
        validate_event_keys([ev])
        assert False, "Expected ValueError for missing key"
    except ValueError as e:
        assert "missing" in str(e)


def test_validate_event_keys_extra():
    ev = make_event()
    ev["extra_field"] = 123
    try:
        validate_event_keys([ev])
        assert False, "Expected ValueError for extra key"
    except ValueError as e:
        assert "extra" in str(e)
