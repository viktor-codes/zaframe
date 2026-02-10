import types

from app.services.service import _compute_limits


class DummyService:
    def __init__(self, soft_limit_ratio: float, hard_limit_ratio: float) -> None:
        self.soft_limit_ratio = soft_limit_ratio
        self.hard_limit_ratio = hard_limit_ratio


def test_compute_limits_basic():
    service = DummyService(soft_limit_ratio=1.0, hard_limit_ratio=1.5)
    soft, hard = _compute_limits(service, max_capacity=10)
    assert soft == 10
    assert hard == 15


def test_compute_limits_with_fractional_ratios():
    service = DummyService(soft_limit_ratio=1.2, hard_limit_ratio=1.5)
    soft, hard = _compute_limits(service, max_capacity=10)
    # 1.2 * 10 = 12.0 -> 12
    # 1.5 * 10 = 15.0 -> 15
    assert soft == 12
    assert hard == 15

