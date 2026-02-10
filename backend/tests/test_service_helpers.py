from datetime import date

from app.models.service import Service


class DummyService:
    """
    Упрощённый объект, на котором можно вызывать Service.get_capacity_status.
    """

    def __init__(self, soft_limit_ratio: float, hard_limit_ratio: float) -> None:
        self.soft_limit_ratio = soft_limit_ratio
        self.hard_limit_ratio = hard_limit_ratio


def test_get_capacity_status_basic_limits():
    service_like = DummyService(soft_limit_ratio=1.0, hard_limit_ratio=1.5)
    # Используем метод Service как функцию, передавая кастомный self
    status = Service.get_capacity_status(
        service_like, max_capacity=10, current_bookings=9, requested=1
    )
    assert status is None  # ровно по soft-лимиту

    status = Service.get_capacity_status(
        service_like, max_capacity=10, current_bookings=10, requested=1
    )
    assert status == "SOFT_LIMIT_REACHED"

    status = Service.get_capacity_status(
        service_like, max_capacity=10, current_bookings=15, requested=1
    )
    assert status == "HARD_LIMIT_REACHED"


def test_get_capacity_status_fractional_ratios():
    service_like = DummyService(soft_limit_ratio=1.2, hard_limit_ratio=1.5)
    # soft = int(1.2 * 10) = 12, hard = int(1.5 * 10) = 15
    status = Service.get_capacity_status(
        service_like, max_capacity=10, current_bookings=11, requested=1
    )
    assert status is None  # total = 12, на границе soft

    status = Service.get_capacity_status(
        service_like, max_capacity=10, current_bookings=12, requested=1
    )
    assert status == "SOFT_LIMIT_REACHED"  # total = 13 > 12


