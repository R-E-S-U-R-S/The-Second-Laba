"""CLI для потокового анализа CSV и JSONL."""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path
from typing import Sequence

from .analysis import Analyzer
from .errors import InvalidEventError, StreamStatsError
from .models import parse_event
from .parsers import iter_records
from .report import write_report

logger = logging.getLogger("streamstats")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="streamstats", description="Потоковый анализ событий CSV/JSONL")
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze = subparsers.add_parser("analyze", help="проанализировать входные файлы")
    analyze.add_argument("input", nargs="+", help="один или несколько входных файлов")
    analyze.add_argument("--format", required=True, choices=("csv", "jsonl"), dest="input_format")
    analyze.add_argument("--output", default="report.json", help="путь к JSON-отчёту (по умолчанию report.json)")
    analyze.add_argument("--skip-invalid", action="store_true", help="пропускать некорректные записи")
    return parser


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s",
        stream=sys.stderr,
        force=True,
    )


def analyze_files(inputs: Sequence[str], input_format: str, output: str, skip_invalid: bool) -> int:
    analyzer = Analyzer()
    for input_name in inputs:
        path = Path(input_name)
        try:
            for raw in iter_records(path, input_format):
                try:
                    if raw.error_message is not None:
                        raise InvalidEventError(raw.error_message)
                    event = parse_event(raw.data)
                except InvalidEventError as exc:
                    message = f"{raw.path}:{raw.line_number}: {exc}"
                    if not skip_invalid:
                        logger.error(message)
                        return 2
                    analyzer.mark_skipped()
                    logger.warning("%s — запись пропущена", message)
                    continue
                analyzer.add(event)
        except StreamStatsError as exc:
            logger.error("%s: %s", path, exc)
            return 2
        except (OSError, UnicodeError, csv.Error) as exc:
            logger.error("ошибка чтения %s: %s", path, exc)
            return 2

    try:
        write_report(analyzer.to_dict(), output)
    except OSError as exc:
        logger.error("не удалось записать отчёт %s: %s", output, exc)
        return 2
    logger.info("Обработано событий: %d; пропущено строк: %d", analyzer.total_events, analyzer.skipped_invalid)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    _configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "analyze":
        return analyze_files(args.input, args.input_format, args.output, args.skip_invalid)
    parser.error("неизвестная команда")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
