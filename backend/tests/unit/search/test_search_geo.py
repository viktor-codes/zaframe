"""Unit tests for search geo helpers."""

from __future__ import annotations

import math

from app.modules.search.repository import geo_bounding_box_deltas


def test_geo_bounding_box_lng_delta_grows_near_poles() -> None:
    """Near the poles, one km spans more longitude degrees than at the equator."""
    _, lng_eq = geo_bounding_box_deltas(lat=0.0, radius_km=10)
    _, lng_high = geo_bounding_box_deltas(lat=60.0, radius_km=10)
    assert lng_high > lng_eq
    assert math.isclose(lng_eq, 10 / 111.0, rel_tol=1e-6)


def test_geo_bounding_box_lat_delta_is_stable() -> None:
    lat_delta, _ = geo_bounding_box_deltas(lat=45.0, radius_km=10)
    assert math.isclose(lat_delta, 10 / 111.0, rel_tol=1e-9)
