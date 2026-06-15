"""
Integration tests for POST /studios/{id}/generate-occurrences.

Validates Pydantic boundary (422) and happy-path slot generation.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import authenticate_via_otp

VALID_PAYLOAD_BASE = {
    "days": [1, 3],
    "start_time": "18:00:00",
    "weeks_count": 2,
}


async def _create_studio_and_course_service(
    client: AsyncClient,
    email: str = "schedule-owner@example.com",
) -> tuple[dict[str, str], int, int]:
    data = await authenticate_via_otp(client, email=email, name="ScheduleTemplate Owner")
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "ScheduleTemplate Studio",
            "description": "For generate-occurrences tests",
            "email": "schedule-studio@example.com",
            "address": "ScheduleTemplate street 1",
            "timezone": "Europe/Dublin",
        },
        headers=headers,
    )
    assert r_studio.status_code == 201
    studio_id = r_studio.json()["id"]

    r_service = await client.post(
        "/api/v1/services",
        json={
            "studio_id": studio_id,
            "name": "Evening Yoga Course",
            "type": "course",
            "duration_minutes": 60,
            "max_capacity": 10,
            "price_single_cents": 1500,
            "price_course_cents": 8000,
        },
        headers=headers,
    )
    assert r_service.status_code == 201
    service_id = r_service.json()["id"]
    return headers, studio_id, service_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_schedule_happy_path(client: AsyncClient):
    headers, studio_id, service_id = await _create_studio_and_course_service(client)

    payload = {**VALID_PAYLOAD_BASE, "service_id": service_id}
    response = await client.post(
        f"/api/v1/studios/{studio_id}/generate-occurrences",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 200
    occurrences = response.json()
    assert isinstance(occurrences, list)
    assert len(occurrences) > 0
    assert all(s["studio_id"] == studio_id for s in occurrences)
    assert all(s["status"] == "active" for s in occurrences)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("payload_override", "case"),
    [
        ({"days": [7]}, "day_of_week_out_of_range"),
        ({"days": []}, "empty_days"),
        ({"days": [1, 1]}, "duplicate_days"),
        ({"start_time": "25:99:00"}, "invalid_start_time"),
        ({"weeks_count": 0}, "weeks_count_too_low"),
        ({"weeks_count": 53}, "weeks_count_too_high"),
        ({"service_id": "not-an-int"}, "invalid_service_id_type"),
    ],
)
async def test_generate_schedule_invalid_payload_returns_422(
    client: AsyncClient,
    payload_override: dict,
    case: str,
):
    headers, studio_id, service_id = await _create_studio_and_course_service(
        client,
        email=f"schedule-422-{case}@example.com",
    )

    payload = {**VALID_PAYLOAD_BASE, "service_id": service_id, **payload_override}
    response = await client.post(
        f"/api/v1/studios/{studio_id}/generate-occurrences",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 422, f"expected 422 for case={case}, body={response.text}"
