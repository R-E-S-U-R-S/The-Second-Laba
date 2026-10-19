"""Потоковый анализатор событий CSV и JSONL."""

from .analysis import Analyzer
from .models import Event, parse_event

__all__ = ["Analyzer", "Event", "parse_event"]
__version__ = "1.0.0"
