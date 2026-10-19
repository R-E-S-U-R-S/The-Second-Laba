"""Потоковые парсеры CSV и JSONL."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, TextIO

from .errors import UnsupportedFormatError


@dataclass(frozen=True, slots=True)
class RawRecord:
    """Сырая запись и её исходное расположение."""

    data: dict[str, Any]
    path: Path
    line_number: int
    error_message: str | None = None


def _jsonl_records(file: TextIO, path: Path) -> Iterator[RawRecord]:
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


def _csv_records(file: TextIO, path: Path) -> Iterator[RawRecord]:
    reader = csv.DictReader(file)
    # Инициализировать заголовок отдельно, чтобы номер первой записи был 2.
    _ = reader.fieldnames
    previous_end_line = reader.line_num
    for row in reader:
        # line_num учитывает физические строки, в том числе поля CSV с переводами строк.
        start_line = previous_end_line + 1
        previous_end_line = reader.line_num
        if None in row:
            yield RawRecord(
                data={}, path=path, line_number=start_line,
                error_message="в записи больше значений, чем столбцов в заголовке",
            )
            continue
        # DictReader даёт None для отсутствующих значений в неполной строке;
        # оставляем их для общей валидации модели.
        yield RawRecord(data=dict(row), path=path, line_number=start_line)


def iter_records(path: str | Path, input_format: str) -> Iterator[RawRecord]:
    """Итерировать записи файла, не загружая файл целиком в память."""
    file_path = Path(path)
    fmt = input_format.lower()
    if fmt not in {"csv", "jsonl"}:
        raise UnsupportedFormatError(f"неподдерживаемый формат: {input_format!r}")

    with file_path.open("r", encoding="utf-8", newline="") as file:
        if fmt == "csv":
            yield from _csv_records(file, file_path)
        else:
            yield from _jsonl_records(file, file_path)
