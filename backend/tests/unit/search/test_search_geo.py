"""Unit tests for search geo helpers and query bounds."""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from app.modules.search.repository import (
    _clamp_limit,
    _clamp_radius_km,
    geo_bounding_box_deltas,
)
from app.modules.search.schemas import SearchQueryParams


def test_geo_bounding_box_lng_delta_grows_near_poles() -> None:
    """Near the poles, one km spans more longitude degrees than at the equator."""
    _, lng_eq = geo_bounding_box_deltas(lat=0.0, radius_km=10)
    _, lng_high = geo_bounding_box_deltas(lat=60.0, radius_km=10)
    assert lng_high > lng_eq
    assert math.isclose(lng_eq, 10 / 111.0, rel_tol=1e-6)


def test_geo_bounding_box_lat_delta_is_stable() -> None:
    lat_delta, _ = geo_bounding_box_deltas(lat=45.0, radius_km=10)
    assert math.isclose(lat_delta, 10 / 111.0, rel_tol=1e-9)


def test_clamp_radius_km_bounds() -> None:
    assert _clamp_radius_km(None) == 10.0
    assert _clamp_radius_km(0) == 1.0
    assert _clamp_radius_km(999) == 50.0
    assert _clamp_radius_km(25) == 25.0


def test_clamp_limit_bounds() -> None:
    assert _clamp_limit(None) == 20
    assert _clamp_limit(0) == 1
    assert _clamp_limit(999) == 50
    assert _clamp_limit(10) == 10


def test_search_query_params_rejects_unbounded_radius() -> None:
    with pytest.raises(ValidationError):
        SearchQueryParams(radius_km=0)
    with pytest.raises(ValidationError):
        SearchQueryParams(radius_km=51)


def test_search_query_params_rejects_unbounded_limit() -> None:
    with pytest.raises(ValidationError):
        SearchQueryParams(limit=0)
    with pytest.raises(ValidationError):
        SearchQueryParams(limit=51)
