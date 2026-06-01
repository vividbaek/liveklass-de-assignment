from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import psycopg

from src.db import DB_CONFIG


_QUERY_DIR = Path(__file__).resolve().parent.parent / "sql" / "queries"


def fetch_session_funnel() -> list[tuple[str, int, Decimal, Decimal | None]]:
    query = (_QUERY_DIR / "session_funnel.sql").read_text(encoding="utf-8")
    return [
        (step_name, int(count), from_start, from_previous)
        for step_name, count, from_start, from_previous in _fetch_all(query)
    ]


def fetch_preview_watch_conversion() -> list[tuple[str, int, int, Decimal]]:
    query = (_QUERY_DIR / "preview_watch_conversion.sql").read_text(encoding="utf-8")
    return [
        (bucket, int(preview_count), int(purchase_count), conversion_rate)
        for bucket, preview_count, purchase_count, conversion_rate in _fetch_all(query)
    ]


def fetch_course_revenue() -> list[tuple[str, int, int]]:
    query = (_QUERY_DIR / "course_revenue.sql").read_text(encoding="utf-8")
    return [
        (course_id, int(purchase_count), int(total_revenue))
        for course_id, purchase_count, total_revenue in _fetch_all(query)
    ]


def fetch_error_area_counts() -> list[tuple[str, int]]:
    query = (_QUERY_DIR / "error_area_counts.sql").read_text(encoding="utf-8")
    return [(error_area, int(count)) for error_area, count in _fetch_all(query)]


def _fetch_all(query: str) -> list[tuple]:
    with psycopg.connect(**DB_CONFIG) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()
