# SQLAlchemy ORM models
# Модели БД будут добавлены в Фазе 1 (User, Studio, Slot, Booking)

# Экспортируем Base для использования в моделях и Alembic
from app.core.database import Base

__all__ = ["Base"]
