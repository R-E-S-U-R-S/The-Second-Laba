from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from streamstats.analysis import Analyzer
from streamstats.errors import InvalidEventError, InvalidTimestampError
from streamstats.models import parse_event
from streamstats.parser import iter_records
from streamstats.report import report_json, write_report
from streamstats.__main__ import main


def valid_record(**overrides):
    record = {
        "timestamp": "2025-01-02T03:04:05+00:00",
        "level": "INFO",
        "source": "service-a",
        "message": "Тестовое сообщение",
    }
    record.update(overrides)
    return record


def write_jsonl(path: Path, records: list[object]) -> Path:
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )
    return path


def test_parse_valid_event_and_unicode():
    event = parse_event(valid_record(message="Ошибка в модуле: привет"))
    assert event.level == "INFO"
    assert event.source == "service-a"
    assert event.message == "Ошибка в модуле: привет"
    assert event.timestamp.tzinfo is not None


@pytest.mark.parametrize(
    "record",
    [
        {"level": "INFO", "source": "svc", "message": "missing timestamp"},
        valid_record(level="TRACE"),
        valid_record(source="  "),
        valid_record(message=123),
    ],
)
def test_parse_event_rejects_invalid_fields(record):
    with pytest.raises(InvalidEventError):
        parse_event(record)


@pytest.mark.parametrize(
    "timestamp",
    ["", "not-a-date", "2025-01-02T03:04:05"],
)
def test_parse_event_rejects_invalid_or_timezone_naive_timestamp(timestamp):
    with pytest.raises(InvalidTimestampError):
        parse_event(valid_record(timestamp=timestamp))


def test_analyzer_aggregates_levels_sources_and_error_top():
    analyzer = Analyzer()
    events = [
        valid_record(level="ERROR", source="alpha"),
        valid_record(level="CRITICAL", source="alpha"),
        valid_record(level="ERROR", source="beta"),
        valid_record(level="INFO", source="beta"),
    ]
    for record in events:
        analyzer.add(parse_event(record))

    report = analyzer.to_dict()
    assert report["total_events"] == 4
    assert report["by_level"] == {"CRITICAL": 1, "ERROR": 2, "INFO": 1}
    assert report["by_source"] == {"alpha": 2, "beta": 2}
    assert report["top_error_sources"] == [
        {"source": "alpha", "count": 2},
        {"source": "beta", "count": 1},
    ]


def test_analyzer_uses_chronological_bounds_and_counts_skips():
    analyzer = Analyzer()
    analyzer.add(parse_event(valid_record(timestamp="2025-01-02T10:00:00+02:00")))
    analyzer.add(parse_event(valid_record(timestamp="2025-01-02T07:00:00+00:00")))
    analyzer.mark_skipped()

    report = analyzer.to_dict()
    assert datetime.fromisoformat(report["first_timestamp"]).astimezone(timezone.utc) == (
        datetime(2025, 1, 2, 7, 0, tzinfo=timezone.utc)
    )
    assert datetime.fromisoformat(report["last_timestamp"]).astimezone(timezone.utc) == (
        datetime(2025, 1, 2, 8, 0, tzinfo=timezone.utc)
    )
    assert report["skipped_invalid"] == 1


def test_jsonl_reader_yields_records_and_one_based_line_numbers(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text(
        '{"timestamp":"2025-01-01T00:00:00Z","level":"INFO","source":"svc","message":"ok"}\n'
        '{broken json}\n',
        encoding="utf-8",
    )

    records = list(iter_records(path, "jsonl"))
    assert len(records) == 2
    assert records[0].line_number == 1
    assert records[0].data["source"] == "svc"
    assert records[1].line_number == 2
    assert records[1].error_message is not None


def test_csv_reader_handles_quoted_commas_and_unicode(tmp_path):
    path = tmp_path / "events.csv"
    path.write_text(
        "timestamp,level,source,message\n"
        '2025-01-01T00:00:00Z,INFO,svc,"привет, мир"\n',
        encoding="utf-8",
    )

    records = list(iter_records(path, "csv"))
    assert len(records) == 1
    assert records[0].data["message"] == "привет, мир"


def test_report_json_is_valid_and_preserves_unicode(tmp_path):
    report = {"message": "Привет, мир", "total_events": 1}
    serialized = report_json(report)
    assert json.loads(serialized) == report
    assert "Привет" in serialized

    output = tmp_path / "report.json"
    write_report(report, output)
    assert json.loads(output.read_text(encoding="utf-8")) == report


def test_cli_analyzes_valid_jsonl(tmp_path):
    input_path = write_jsonl(tmp_path / "events.jsonl", [valid_record()])
    output_path = tmp_path / "report.json"

    code = main([
        "analyze", str(input_path),
        "--format", "jsonl",
        "--output", str(output_path),
    ])

    assert code == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["total_events"] == 1
    assert report["by_level"] == {"INFO": 1}


def test_cli_skip_invalid_continues_after_invalid_timestamp(tmp_path):
    input_path = write_jsonl(
        tmp_path / "events.jsonl",
        [
            valid_record(),
            valid_record(timestamp="not-a-date"),
            valid_record(level="ERROR", source="service-b"),
        ],
    )
    output_path = tmp_path / "report.json"

    code = main([
        "analyze", str(input_path),
        "--format", "jsonl",
        "--output", str(output_path),
        "--skip-invalid",
    ])

    assert code == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["total_events"] == 2
    assert report["skipped_invalid"] == 1


def test_cli_multiple_files_accumulates_statistics(tmp_path):
    first = write_jsonl(tmp_path / "first.jsonl", [valid_record(source="first")])
    second = write_jsonl(tmp_path / "second.jsonl", [valid_record(source="second")])
    output_path = tmp_path / "report.json"

    code = main([
        "analyze", str(first), str(second),
        "--format", "jsonl",
        "--output", str(output_path),
    ])

    assert code == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["total_events"] == 2
    assert report["by_source"] == {"first": 1, "second": 1}


def test_cli_returns_two_for_missing_input_file(tmp_path):
    output_path = tmp_path / "report.json"
    code = main([
        "analyze", str(tmp_path / "missing.jsonl"),
        "--format", "jsonl",
        "--output", str(output_path),
    ])
    assert code == 2
    assert not output_path.exists()
