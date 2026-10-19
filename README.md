# StreamStats — лабораторная работа № 2

Пакет `streamstats` потоково анализирует события в CSV и JSONL, проверяет записи и сохраняет статистику в JSON.

## Требования

- Python 3.10 или новее.
- Для разработки: `pytest` и `ruff`.

## Установка

Из каталога проекта:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Запуск

```bash
python -m streamstats --help
python -m streamstats analyze events.csv --format csv --output report.json
python -m streamstats analyze first.jsonl second.jsonl --format jsonl --output report.json
python -m streamstats analyze events.jsonl --format jsonl --skip-invalid
```

`--output` по умолчанию равен `report.json`. При ошибочной записи обычный режим завершает CLI с кодом `2` и сообщает имя файла и номер строки. С `--skip-invalid` некорректные записи пропускаются, для каждой пишется `WARNING`, а их количество попадает в поле `skipped_invalid` отчёта. Ошибки открытия/чтения файлов также приводят к коду `2`.

## Модель события

Каждая запись должна содержать:

- `timestamp`: ISO 8601 со смещением часового пояса, например `2026-10-07T12:00:00+03:00`;
- `level`: `DEBUG`, `INFO`, `WARNING`, `ERROR` или `CRITICAL`;
- `source`: непустая строка;
- `message`: строка.

CSV должен содержать заголовки с именами этих полей. JSONL содержит один JSON-объект на строку.

## Формат отчёта

Отчёт включает `total_events`, `by_level`, `by_source`, `top_error_sources`, `first_timestamp`, `last_timestamp` и `skipped_invalid`. `top_error_sources` — список не более чем из пяти объектов `{"source": ..., "count": ...}`, учитывающий только уровни `ERROR` и `CRITICAL`. При равном количестве ошибок источники сортируются по имени. Для пустого набора временные границы равны `null`.

## Проверки

```bash
python -m pytest
ruff check .
python -m streamstats --help
```

## Архитектура

- `models.py` — модель и валидация событий;
- `parsers.py` — потоковые CSV/JSONL парсеры с номерами исходных строк;
- `analysis.py` — инкрементальные агрегаты;
- `report.py` — JSON-сериализация и запись;
- `errors.py` — семейство исключений;
- `__main__.py` — CLI и обработка ошибок на границе приложения.
