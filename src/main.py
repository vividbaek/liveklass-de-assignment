from __future__ import annotations

import json
from collections import Counter
from typing import Any

from src.enums.event_values import EVENT_COLUMNS
from src.event_generator import generate_events


def main() -> None:
    events = generate_events(target_sessions=250)
    event_counts = Counter(event["event_type"] for event in events)
    session_count = len({event["session_id"] for event in events})

    print(f"Generated {len(events)} synthetic events from {session_count} sessions")
    print()
    print("Event counts by type:")
    for event_type, count in event_counts.most_common():
        print(f"- {event_type}: {count}")

    print()
    print("Sample events:")
    for event in events[:3]:
        print(json.dumps(event, ensure_ascii=False, indent=2, default=_json_default))

    _validate_event_keys(events)


def _validate_event_keys(events: list[dict[str, Any]]) -> None:
    expected_keys = set(EVENT_COLUMNS)

    for event in events:
        event_keys = set(event.keys())
        if event_keys != expected_keys:
            missing_keys = sorted(expected_keys - event_keys)
            extra_keys = sorted(event_keys - expected_keys)
            raise ValueError(
                "Generated event does not match schema keys. "
                f"missing={missing_keys}, extra={extra_keys}"
            )


def _json_default(value: Any) -> str:
    return value.isoformat()


if __name__ == "__main__":
    main()
