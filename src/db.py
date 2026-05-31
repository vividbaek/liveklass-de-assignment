from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import psycopg

from src.enums.event_values import EVENT_COLUMNS


DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "liveklass"),
    "user": os.getenv("POSTGRES_USER", "liveklass"),
    "password": os.getenv("POSTGRES_PASSWORD", "liveklass"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
}

INIT_SQL_PATH = Path(__file__).resolve().parent.parent / "sql" / "init.sql"


def wait_for_database(max_attempts: int = 20, delay_seconds: float = 1.0) -> None:
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            with psycopg.connect(**DB_CONFIG):
                print("PostgreSQL is ready")
                return
        except psycopg.OperationalError as error:
            last_error = error
            print(
                f"Waiting for PostgreSQL... "
                f"attempt {attempt}/{max_attempts}"
            )
            time.sleep(delay_seconds)

    raise RuntimeError("PostgreSQL did not become ready") from last_error


def initialize_schema() -> None:
    init_sql = INIT_SQL_PATH.read_text(encoding="utf-8")

    with psycopg.connect(**DB_CONFIG) as connection:
        with connection.cursor() as cursor:
            cursor.execute(init_sql)

    print("Initialized database schema")


def reset_events_table() -> None:
    with psycopg.connect(**DB_CONFIG) as connection:
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE events;")

    print("Truncated events table")


def insert_events(events: list[dict[str, Any]], batch_size: int = 1000) -> int:
    if not events:
        return 0

    columns = ", ".join(EVENT_COLUMNS)
    placeholders = ", ".join(["%s"] * len(EVENT_COLUMNS))
    insert_sql = f"INSERT INTO events ({columns}) VALUES ({placeholders});"
    inserted_count = 0

    with psycopg.connect(**DB_CONFIG) as connection:
        with connection.cursor() as cursor:
            for batch_number, batch in enumerate(_chunk(events, batch_size), start=1):
                rows = [tuple(event[column] for column in EVENT_COLUMNS) for event in batch]
                cursor.executemany(insert_sql, rows)
                inserted_count += len(batch)
                print(f"Inserted batch {batch_number}: {len(batch)} rows")

    return inserted_count


def count_events() -> int:
    with psycopg.connect(**DB_CONFIG) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM events;")
            row = cursor.fetchone()

    if row is None:
        return 0
    return int(row[0])


def _chunk(events: list[dict[str, Any]], batch_size: int) -> list[list[dict[str, Any]]]:
    return [
        events[index : index + batch_size]
        for index in range(0, len(events), batch_size)
    ]
