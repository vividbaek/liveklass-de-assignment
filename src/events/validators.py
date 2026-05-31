from __future__ import annotations

from typing import Any

from src.enums.event_values import EVENT_COLUMNS


def validate_event_keys(events: list[dict[str, Any]]) -> None:
    """각 이벤트 딕셔너리가 기대된 키 집합과 정확히 일치하는지 검증합니다.

    불일치가 발견되면 상세 정보를 포함한 ValueError를 발생시킵니다.
    """
    expected_keys = set(EVENT_COLUMNS)

    for event in events:
        event_keys = set(event.keys())
        if event_keys != expected_keys:
            missing_keys = sorted(expected_keys - event_keys)
            extra_keys = sorted(event_keys - expected_keys)
            raise ValueError(
                "생성된 이벤트의 key가 스키마와 일치하지 않습니다. "
                f"missing={missing_keys}, extra={extra_keys}"
            )
