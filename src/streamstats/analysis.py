from collections import Counter
from datetime import datetime, timezone
from typing import Any

from .models import Event


class Analyzer:
    """Накопитель статистики; все файлы обрабатываются одним экземпляром."""

    def __init__(self) -> None:
        self.total_events = 0
        self.by_level: Counter[str] = Counter()
        self.by_source: Counter[str] = Counter()
        self.errors_by_source: Counter[str] = Counter()
        self.first_timestamp: datetime | None = None
        self.last_timestamp: datetime | None = None
        self.skipped_invalid = 0

    def add(self, event: Event) -> None:
        """Добавить одно валидное событие в счётчики."""
        self.total_events += 1
        self.by_level[event.level] += 1
        self.by_source[event.source] += 1
        if event.level in {"ERROR", "CRITICAL"}:
            self.errors_by_source[event.source] += 1

        timestamp_utc = event.timestamp.astimezone(timezone.utc)
        if self.first_timestamp is None or timestamp_utc < self.first_timestamp.astimezone(timezone.utc):
            self.first_timestamp = event.timestamp
        if self.last_timestamp is None or timestamp_utc > self.last_timestamp.astimezone(timezone.utc):
            self.last_timestamp = event.timestamp

    def mark_skipped(self) -> None:
        self.skipped_invalid += 1

    def to_dict(self) -> dict[str, Any]:
        """Вернуть JSON-совместимый словарь отчёта."""
        top_errors = sorted(self.errors_by_source.items(), key=lambda item: (-item[1], item[0]))[:5]
        return {
            "total_events": self.total_events,
            "by_level": dict(sorted(self.by_level.items())),
            "by_source": dict(sorted(self.by_source.items())),
            "top_error_sources": [
                {"source": source, "count": count} for source, count in top_errors
            ],
            "first_timestamp": self.first_timestamp.isoformat() if self.first_timestamp else None,
            "last_timestamp": self.last_timestamp.isoformat() if self.last_timestamp else None,
            "skipped_invalid": self.skipped_invalid,
        }