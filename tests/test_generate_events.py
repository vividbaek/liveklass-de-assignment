from src.event_generator import generate_events


def test_generate_events_reproducible_by_seed():
    events1 = generate_events(target_sessions=100, seed=123)
    events2 = generate_events(target_sessions=100, seed=123)

    # 같은 seed를 사용하면 생성되는 이벤트 수가 같아야 합니다.
    assert len(events1) == len(events2)

    # 같은 seed를 사용하면 event_type 순서도 재현 가능해야 합니다.
    types1 = [e["event_type"] for e in events1]
    types2 = [e["event_type"] for e in events2]
    assert types1 == types2
