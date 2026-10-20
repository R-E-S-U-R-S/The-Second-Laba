import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import UnsuportedFormatError


@dataclass(frozen=True)
class RawRecord:
    """Сырая запись и её исходное расположение."""

    data: dict[str, Any]
    path: Path
    line_number: int
    error_message: str | None = None


def jsonl_reader(file, path: Path):
    for line_number, line in enumerate(file, start=1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            yield RawRecord(
                data={}, path=path, line_number=line_number,
                error_message=f"некорректный JSON: {exc.msg}",
            )
            continue
        if not isinstance(value, dict):
            yield RawRecord(
                data={}, path=path, line_number=line_number,
                error_message="JSONL-запись должна быть JSON-объектом",
            )
            continue
        yield RawRecord(data=value, path=path, line_number=line_number)


def csv_reader(file, path: Path):
    reader = csv.DictReader(file)
    previous_end_line = reader.line_num
    for row in reader:
        start_line = previous_end_line + 1
        previous_end_line = reader.line_num
        if None in row:
            yield RawRecord(
                data={}, path=path, line_number=start_line,
                error_message="в записи больше значений, чем столбцов в заголовке",
            )
            continue
        yield RawRecord(data=dict(row), path=path, line_number=start_line)


def iter_records(path: str | Path, input_format: str):
    """Итерировать записи файла, не загружая файл целиком в память."""
    file_path = Path(path)
    fmt = input_format.lower()
    if fmt not in {"csv", "jsonl"}:
        raise UnsuportedFormatError(f"неподдерживаемый формат: {input_format!r}")

    with file_path.open("r", encoding="utf-8", newline="") as file:
        if fmt == "csv":
            yield from csv_reader(file, file_path)
        else:
            yield from jsonl_reader(file, file_path)