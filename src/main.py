from __future__ import annotations

import json
from collections import Counter
from decimal import Decimal
from typing import Any

from src.event_generator import EVENT_COLUMNS, generate_events


def main() -> None:
    events = generate_events(target_count=1000)
    event_counts = Counter(event["event_type"] for event in events)

    print(f"Generated {len(events)} synthetic events")
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
    if isinstance(value, Decimal):
        return str(value)
    return value.isoformat()


if __name__ == "__main__":
    main()
