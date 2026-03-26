"""
Утилиты для работы с датой/временем.

Политика: время слотов и расписаний хранится и сравнивается в UTC
(naive datetime в Python); ввод от API конвертируется в UTC при сохранении.
"""

from datetime import UTC, datetime


def to_naive_utc(dt: datetime) -> datetime:
    """
    Приводит datetime к naive UTC для хранения и сравнения с полями БД.

    Используется для Slot.start_time/end_time и везде, где сравниваем с БД.
    """
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt
