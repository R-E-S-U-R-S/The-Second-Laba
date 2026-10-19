"""Сериализация и сохранение отчётов."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def report_json(report: Mapping[str, Any]) -> str:
    """Сериализовать отчёт в читаемый JSON с сохранением Unicode."""
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def write_report(report: Mapping[str, Any], output_path: str | Path) -> None:
    """Записать отчёт в UTF-8 файл."""
    path = Path(output_path)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(report_json(report))
