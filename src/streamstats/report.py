import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def report_json(report: Mapping[str, Any]) -> str:
    """СОздать отчёт в читаемый JSON."""
    return json.dumps(report, ensure_ascii=False, sort_keys=False) + "\n"


def write_report(report: Mapping[str, Any], output_path: str | Path) -> None:
    """Записать отчёт в UTF-8 файл."""
    path = Path(output_path)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(report_json(report))