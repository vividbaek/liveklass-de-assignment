from __future__ import annotations

import json
from collections import Counter
from typing import Any

from src.db import (
    count_events,
    initialize_schema,
    insert_events,
    reset_events_table,
    wait_for_database,
)
from src.enums.event_values import EVENT_COLUMNS
from src.event_generator import generate_events

TARGET_SESSIONS = 2500
BATCH_SIZE = 1000


def main() -> None:
    wait_for_database()
    initialize_schema()
    reset_events_table()

    events = generate_events(target_sessions=TARGET_SESSIONS)
    event_counts = Counter(event["event_type"] for event in events)
    session_count = len({event["session_id"] for event in events})

    print(f"Generated {len(events)} synthetic events from {session_count} sessions")
    _validate_event_keys(events)
    print()
    print("Event counts by type:")
    for event_type, count in event_counts.most_common():
        print(f"- {event_type}: {count}")

    print()
    print("Sample events:")
    for event in events[:3]:
        print(json.dumps(event, ensure_ascii=False, indent=2, default=_json_default))

    print()
    inserted_count = insert_events(events, batch_size=BATCH_SIZE)
    stored_count = count_events()
    print(f"Inserted {inserted_count} events into PostgreSQL")
    print(f"Events table row count: {stored_count}")

    if stored_count != len(events):
        raise RuntimeError(
            f"Row count mismatch. generated={len(events)}, stored={stored_count}"
        )


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
