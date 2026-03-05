"""
Настройка логирования приложения.

- Единый формат логов для консоли (читаемый текст).
- Уровень из settings.LOG_LEVEL.
- Инициализация при старте приложения (lifespan или main).
"""
import logging
import sys

from app.core.config import settings


def setup_logging() -> None:
    """
    Настраивает корневой логгер приложения.

    Формат: timestamp level name message
    Уровень берётся из settings.LOG_LEVEL (по умолчанию INFO).
    """
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    # Снижаем шум от сторонних библиотек
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
