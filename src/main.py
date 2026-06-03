from __future__ import annotations

import json
from collections import Counter

from src.db import (
    count_events,
    initialize_schema,
    insert_events,
    reset_events_table,
    wait_for_database,
)
from src.event_generator import generate_events
from src.events.validators import validate_event_keys
from src.utils.serialization import json_default
from src.visualize import main as generate_charts

TARGET_SESSIONS = 2500
BATCH_SIZE = 1000


def main() -> None:
    wait_for_database()
    initialize_schema()
    reset_events_table()

    events = generate_events(target_sessions=TARGET_SESSIONS)
    event_counts = Counter(event["event_type"] for event in events)
    session_count = len({event["session_id"] for event in events})

    print(f"{session_count}개 session에서 합성 이벤트 {len(events)}건 생성")
    validate_event_keys(events)
    print()
    print("event_type별 이벤트 수:")
    for event_type, count in event_counts.most_common():
        print(f"- {event_type}: {count}")

    print()
    print("샘플 이벤트:")
    for event in events[:3]:
        print(json.dumps(event, ensure_ascii=False, indent=2, default=json_default))

    print()
    inserted_count = insert_events(events, batch_size=BATCH_SIZE)
    stored_count = count_events()
    print(f"PostgreSQL에 이벤트 {inserted_count}건 적재 완료")
    print(f"events 테이블 행 수: {stored_count}")

    if stored_count != len(events):
        raise RuntimeError(
            f"row count가 일치하지 않습니다. generated={len(events)}, stored={stored_count}"
        )

    print()
    generate_charts()


if __name__ == "__main__":
    main()
