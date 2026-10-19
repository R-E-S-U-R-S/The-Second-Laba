"""Исключения пакета streamstats."""


class StreamStatsError(Exception):
    """Базовая ошибка, которую можно безопасно показать пользователю CLI."""


class UnsupportedFormatError(StreamStatsError):
    """Запрошен неподдерживаемый формат входных данных."""


class InvalidEventError(StreamStatsError):
    """Запись не соответствует модели события или не разбирается."""


class InvalidTimestampError(InvalidEventError):
    """Поле timestamp отсутствует или содержит некорректное время."""


class CLIConfigurationError(StreamStatsError):
    """Некорректная конфигурация командной строки."""
