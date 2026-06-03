from src.event_generator import generate_events


def test_generate_events_reproducible_by_seed():
    events1 = generate_events(target_sessions=100, seed=123)
    events2 = generate_events(target_sessions=100, seed=123)

    # 같은 seed를 사용하면 event_id, session_id, event_time까지 재현 가능해야 합니다.
    assert events1 == events2


def test_generate_events_approx_target_count_is_session_based():
    events = generate_events(approx_target_count=100, seed=123)

    assert len({event["session_id"] for event in events}) == 25
    assert 80 <= len(events) <= 120
