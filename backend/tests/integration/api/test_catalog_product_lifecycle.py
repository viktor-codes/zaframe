"""FR-07 catalog product lifecycle and behavior contracts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from tests.conftest import authenticate_via_otp, create_test_service


async def _owner_headers(client: AsyncClient, *, email: str) -> dict[str, str]:
    data = await authenticate_via_otp(client, email=email, name="Catalog Owner")
    return {"Authorization": f"Bearer {data['access_token']}"}


async def _create_studio(
    client: AsyncClient,
    *,
    headers: dict[str, str],
    name: str = "Lifecycle Studio",
    slug: str | None = None,
    cancel_before_hours: int = 24,
) -> int:
    slug = slug or f"lifecycle-studio-{uuid4().hex[:8]}"
    response = await client.post(
        "/api/v1/studios",
        json={
            "name": name,
            "slug": slug,
            "description": "FR-07 contract tests",
            "email": f"{slug}@example.com",
            "timezone": "Europe/Dublin",
            "cancel_before_hours": cancel_before_hours,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_service(
    client: AsyncClient,
    *,
    headers: dict[str, str],
    studio_id: int,
    name: str,
    visibility: str = "published",
    type_: str = "single",
) -> int:
    response = await client.post(
        "/api/v1/services",
        json={
            "studio_id": studio_id,
            "name": name,
            "type": type_,
            "duration_minutes": 60,
            "max_capacity": 5,
            "price_single_cents": 1000,
            "price_course_cents": 4000 if type_ == "course" else None,
            "visibility": visibility,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_occurrence(
    client: AsyncClient,
    *,
    headers: dict[str, str],
    studio_id: int,
    service_id: int,
    start_time: datetime | None = None,
) -> int:
    start = start_time or (datetime.now(UTC) + timedelta(hours=4))
    response = await client.post(
        "/api/v1/occurrences",
        json={
            "studio_id": studio_id,
            "service_id": service_id,
            "start_time": start.isoformat(),
            "end_time": (start + timedelta(hours=1)).isoformat(),
            "title": "Lifecycle Occurrence",
            "max_capacity": 5,
            "price_cents": 1000,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_booking(
    client: AsyncClient,
    *,
    occurrence_id: int,
    guest_email: str = "fr07-guest@example.com",
) -> int:
    response = await client.post(
        "/api/v1/bookings",
        json={
            "occurrence_id": occurrence_id,
            "guest_name": "FR07 Guest",
            "guest_email": guest_email,
            "guest_phone": "+111111111",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_studio_timezone_must_be_iana_string(client: AsyncClient) -> None:
    headers = await _owner_headers(client, email="fr07-timezone-owner@example.com")

    response = await client.post(
        "/api/v1/studios",
        json={
            "name": "Invalid Timezone Studio",
            "slug": "fr07-invalid-timezone-studio",
            "timezone": "Not/A_Real_Zone",
        },
        headers=headers,
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_public_catalog_shows_only_published_services_and_owner_sees_all(
    client: AsyncClient,
) -> None:
    headers = await _owner_headers(client, email="fr07-visibility-owner@example.com")
    slug = f"fr07-visibility-studio-{uuid4().hex[:8]}"
    studio_id = await _create_studio(
        client,
        headers=headers,
        slug=slug,
    )

    await _create_service(
        client,
        headers=headers,
        studio_id=studio_id,
        name="Draft Service",
        visibility="draft",
    )
    published_id = await _create_service(
        client,
        headers=headers,
        studio_id=studio_id,
        name="Published Service",
        visibility="published",
    )
    await _create_service(
        client,
        headers=headers,
        studio_id=studio_id,
        name="Archived Service",
        visibility="archived",
    )

    public_response = await client.get(f"/api/v1/studios/slug/{slug}/public")
    assert public_response.status_code == 200, public_response.text
    public_services = public_response.json()["services"]
    assert [service["id"] for service in public_services] == [published_id]

    owner_response = await client.get(f"/api/v1/studios/{studio_id}/services", headers=headers)
    assert owner_response.status_code == 200, owner_response.text
    assert {service["visibility"] for service in owner_response.json()["items"]} == {
        "draft",
        "published",
        "archived",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_direct_public_service_reads_hide_draft_but_owner_can_preview(
    client: AsyncClient,
) -> None:
    headers = await _owner_headers(client, email="fr07-direct-draft-owner@example.com")
    studio_id = await _create_studio(client, headers=headers)
    service_id = await _create_service(
        client,
        headers=headers,
        studio_id=studio_id,
        name="Draft Course",
        visibility="draft",
        type_="course",
    )
    await _create_occurrence(
        client,
        headers=headers,
        studio_id=studio_id,
        service_id=service_id,
    )
    schedule_response = await client.post(
        f"/api/v1/services/{service_id}/schedule-templates",
        json={
            "day_of_week": 1,
            "start_time": "18:00:00",
            "valid_from": "2026-06-01",
        },
        headers=headers,
    )
    assert schedule_response.status_code == 201, schedule_response.text

    public_detail = await client.get(f"/api/v1/services/{service_id}")
    public_availability = await client.get(f"/api/v1/services/{service_id}/availability")
    public_schedules = await client.get(f"/api/v1/services/{service_id}/schedule-templates")

    assert public_detail.status_code == 404
    assert public_availability.status_code == 404
    assert public_schedules.status_code == 404

    owner_detail = await client.get(f"/api/v1/services/{service_id}", headers=headers)
    owner_availability = await client.get(
        f"/api/v1/services/{service_id}/availability",
        headers=headers,
    )
    owner_schedules = await client.get(
        f"/api/v1/services/{service_id}/schedule-templates",
        headers=headers,
    )

    assert owner_detail.status_code == 200, owner_detail.text
    assert owner_detail.json()["visibility"] == "draft"
    assert owner_availability.status_code == 200, owner_availability.text
    assert owner_schedules.status_code == 200, owner_schedules.text
    assert len(owner_schedules.json()["items"]) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_archived_service_occurrence_is_not_bookable(client: AsyncClient) -> None:
    headers = await _owner_headers(client, email="fr07-archived-owner@example.com")
    studio_id = await _create_studio(client, headers=headers)
    service_id = await _create_service(
        client,
        headers=headers,
        studio_id=studio_id,
        name="Archived Class",
        visibility="archived",
    )
    occurrence_id = await _create_occurrence(
        client,
        headers=headers,
        studio_id=studio_id,
        service_id=service_id,
    )

    response = await client.post(
        "/api/v1/bookings",
        json={
            "occurrence_id": occurrence_id,
            "guest_name": "Archived Guest",
            "guest_email": "archived-guest@example.com",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Occurrence is not available for booking"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_deleting_occurrence_with_booking_preserves_cancelled_history(
    client: AsyncClient,
) -> None:
    headers = await _owner_headers(client, email="fr07-delete-owner@example.com")
    studio_id = await _create_studio(client, headers=headers)
    service_id = await create_test_service(
        client,
        headers=headers,
        studio_id=studio_id,
        name="Delete With Booking",
    )
    occurrence_id = await _create_occurrence(
        client,
        headers=headers,
        studio_id=studio_id,
        service_id=service_id,
    )
    await _create_booking(
        client, occurrence_id=occurrence_id, guest_email="delete-guest@example.com"
    )

    delete_response = await client.delete(f"/api/v1/occurrences/{occurrence_id}", headers=headers)
    assert delete_response.status_code == 204, delete_response.text

    occurrence_response = await client.get(f"/api/v1/occurrences/{occurrence_id}")
    assert occurrence_response.status_code == 200
    occurrence = occurrence_response.json()
    assert occurrence["status"] == "cancelled"
    assert occurrence["cancelled_at"] is not None
    assert occurrence["cancellation_reason"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_customer_cancellation_cutoff_blocks_late_cancel_but_owner_can_bypass(
    client: AsyncClient,
) -> None:
    headers = await _owner_headers(client, email="fr07-cutoff-owner@example.com")
    studio_id = await _create_studio(
        client,
        headers=headers,
        cancel_before_hours=24,
    )
    service_id = await create_test_service(
        client,
        headers=headers,
        studio_id=studio_id,
        name="Cutoff Class",
    )
    occurrence_id = await _create_occurrence(
        client,
        headers=headers,
        studio_id=studio_id,
        service_id=service_id,
        start_time=datetime.now(UTC) + timedelta(hours=2),
    )
    guest_email = "cutoff-guest@example.com"
    booking_id = await _create_booking(client, occurrence_id=occurrence_id, guest_email=guest_email)

    guest_data = await authenticate_via_otp(client, email=guest_email, name="Cutoff Guest")
    guest_headers = {"Authorization": f"Bearer {guest_data['access_token']}"}
    guest_cancel = await client.patch(
        f"/api/v1/bookings/{booking_id}/cancel", headers=guest_headers
    )
    assert guest_cancel.status_code == 403

    owner_cancel = await client.patch(f"/api/v1/bookings/{booking_id}/cancel", headers=headers)
    assert owner_cancel.status_code == 200, owner_cancel.text
    assert owner_cancel.json()["status"] == "cancelled"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_schedule_template_edit_does_not_mutate_generated_occurrences(
    client: AsyncClient,
) -> None:
    headers = await _owner_headers(client, email="fr07-schedule-owner@example.com")
    studio_id = await _create_studio(client, headers=headers)
    service_id = await _create_service(
        client,
        headers=headers,
        studio_id=studio_id,
        name="Schedule Course",
        type_="course",
    )

    template_response = await client.post(
        f"/api/v1/services/{service_id}/schedule-templates",
        json={
            "day_of_week": 1,
            "start_time": "18:00:00",
            "valid_from": "2026-06-01",
        },
        headers=headers,
    )
    assert template_response.status_code == 201, template_response.text
    template = template_response.json()
    assert (
        "Already generated occurrences are not changed automatically" in template["edit_behavior"]
    )

    generate_response = await client.post(
        f"/api/v1/studios/{studio_id}/generate-occurrences",
        json={
            "service_id": service_id,
            "days": [0, 1, 2, 3, 4, 5, 6],
            "start_time": "18:00:00",
            "weeks_count": 1,
        },
        headers=headers,
    )
    assert generate_response.status_code == 200, generate_response.text
    occurrence = generate_response.json()[0]
    original_start = occurrence["start_time"]

    update_response = await client.patch(
        f"/api/v1/services/schedule-templates/{template['id']}",
        json={"start_time": "20:00:00"},
        headers=headers,
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["start_time"] == "20:00:00"

    occurrence_response = await client.get(f"/api/v1/occurrences/{occurrence['id']}")
    assert occurrence_response.status_code == 200
    assert occurrence_response.json()["start_time"] == original_start
