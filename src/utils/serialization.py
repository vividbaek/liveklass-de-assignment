from __future__ import annotations

from typing import Any


def json_default(value: Any) -> str:
    """`json.dumps`에서 사용되는 기본 JSON 직렬화 함수입니다.

    현재는 `isoformat`을 가진 날짜/시간 객체를 직렬화하는 용도로 사용됩니다.
    """
    return value.isoformat()
