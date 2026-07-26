"""Unit tests for /metrics authorization helper."""

import pytest

from app.api.metrics import _authorize_metrics
from app.core.config import settings
from app.core.exceptions import AppError


def test_authorize_metrics_open_in_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "dev")
    monkeypatch.setattr(settings, "METRICS_TOKEN", None)
    _authorize_metrics(None)


def test_authorize_metrics_requires_configured_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")
    monkeypatch.setattr(settings, "METRICS_TOKEN", None)
    with pytest.raises(AppError) as exc:
        _authorize_metrics("Bearer anything")
    assert exc.value.status_code == 503


def test_authorize_metrics_accepts_matching_bearer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "METRICS_TOKEN", "secret-token")
    _authorize_metrics("Bearer secret-token")


def test_authorize_metrics_rejects_wrong_bearer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "METRICS_TOKEN", "secret-token")
    with pytest.raises(AppError) as exc:
        _authorize_metrics("Bearer other")
    assert exc.value.status_code == 401
