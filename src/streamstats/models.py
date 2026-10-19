"""Модель события и валидация полей."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from .errors import InvalidEventError, InvalidTimestampError

VALID_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
REQUIRED_FIELDS = ("timestamp", "level", "source", "message")


@dataclass(frozen=True, slots=True)
class Event:
    """Проверенное событие. timestamp содержит aware datetime."""

    timestamp: datetime
    timestamp_text: str
    level: str
    source: str
    message: str


def parse_event(record: Mapping[str, Any]) -> Event:
    """Проверить сырую запись и преобразовать её в Event."""
    if not isinstance(record, Mapping):
        raise InvalidEventError("событие должно быть объектом с именованными полями")

    missing = [field for field in REQUIRED_FIELDS if field not in record]
    if missing:
        raise InvalidEventError(f"отсутствуют обязательные поля: {', '.join(missing)}")

    timestamp_value = record["timestamp"]
    if not isinstance(timestamp_value, str) or not timestamp_value.strip():
        raise InvalidTimestampError("timestamp должен быть непустой строкой ISO 8601")
    timestamp_text = timestamp_value.strip()
    try:
        # fromisoformat понимает смещение часового пояса и дробные секунды.
        timestamp = datetime.fromisoformat(timestamp_text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidTimestampError(f"некорректный timestamp {timestamp_text!r}: {exc}") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise InvalidTimestampError("timestamp должен содержать смещение часового пояса")

    level = record["level"]
    if not isinstance(level, str) or level not in VALID_LEVELS:
        raise InvalidEventError(
            "level должен быть одним из значений: " + ", ".join(sorted(VALID_LEVELS))
        )

    source = record["source"]
    if not isinstance(source, str) or not source.strip():
        raise InvalidEventError("source должен быть непустой строкой")

    message = record["message"]
    if not isinstance(message, str):
        raise InvalidEventError("message должен быть строкой")

    return Event(
        timestamp=timestamp,
        timestamp_text=timestamp_text,
        level=level,
        source=source.strip(),
        message=message,
    )
