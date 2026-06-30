from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from tests.conftest import authenticate_via_otp


async def _auth_headers(
    client: AsyncClient,
    *,
    email: str,
    name: str = "Owner User",
) -> dict[str, str]:
    data = await authenticate_via_otp(client, email=email, name=name)
    return {"Authorization": f"Bearer {data['access_token']}"}


async def _create_studio(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    name: str,
    slug: str,
) -> dict:
    response = await client.post(
        "/api/v1/studios",
        json={
            "name": name,
            "slug": slug,
            "description": "Frontend readiness studio",
            "logo_url": f"https://cdn.example.com/{slug}/logo.png",
            "cover_url": f"https://cdn.example.com/{slug}/cover.jpg",
            "timezone": "Europe/Dublin",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _create_course_service(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    studio_id: int,
    name: str = "Frontend Course",
) -> dict:
    response = await client.post(
        "/api/v1/services",
        json={
            "studio_id": studio_id,
            "name": name,
            "type": "course",
            "duration_minutes": 60,
            "max_capacity": 10,
            "price_single_cents": 1500,
            "price_course_cents": 8000,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _create_occurrence(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    studio_id: int,
    service_id: int,
    starts_in_days: int,
) -> int:
    start_time = datetime.now(UTC) + timedelta(days=starts_in_days)
    response = await client.post(
        "/api/v1/occurrences",
        json={
            "studio_id": studio_id,
            "service_id": service_id,
            "start_time": start_time.isoformat(),
            "end_time": (start_time + timedelta(hours=1)).isoformat(),
            "title": "Frontend readiness session",
            "max_capacity": 10,
            "price_cents": 1500,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_patch_auth_me_updates_only_editable_profile_fields(client: AsyncClient):
    suffix = uuid4().hex[:8]
    email = f"fr01-profile-{suffix}@example.com"
    headers = await _auth_headers(
        client,
        email=email,
        name="Original Name",
    )

    update_response = await client.patch(
        "/api/v1/auth/me",
        json={"name": "Updated Name", "phone": "+353871234567", "marketing_consent": True},
        headers=headers,
    )
    assert update_response.status_code == 200
    profile = update_response.json()
    assert profile["email"] == email
    assert profile["name"] == "Updated Name"
    assert profile["phone"] == "+353871234567"
    assert profile["marketing_consent"] is True

    protected_response = await client.patch(
        "/api/v1/auth/me",
        json={"email": "attacker@example.com", "role": "admin"},
        headers=headers,
    )
    assert protected_response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_studios_my_slug_media_and_slug_conflict(client: AsyncClient):
    suffix = uuid4().hex[:8]
    owner_headers = await _auth_headers(client, email=f"fr01-owner-{suffix}@example.com")
    other_headers = await _auth_headers(
        client,
        email=f"fr01-other-owner-{suffix}@example.com",
    )
    slug = f"fr01-studio-{suffix}"

    studio = await _create_studio(
        client,
        owner_headers,
        name="FR01 Studio",
        slug=slug,
    )
    assert studio["slug"] == slug
    assert studio["logo_url"].endswith("/logo.png")
    assert studio["cover_url"].endswith("/cover.jpg")

    my_response = await client.get("/api/v1/studios/my", headers=owner_headers)
    assert my_response.status_code == 200
    assert [item["id"] for item in my_response.json()] == [studio["id"]]

    other_response = await client.get("/api/v1/studios/my", headers=other_headers)
    assert other_response.status_code == 200
    assert other_response.json() == []

    duplicate_response = await client.post(
        "/api/v1/studios",
        json={
            "name": "Duplicate Slug",
            "slug": slug,
            "timezone": "Europe/Dublin",
        },
        headers=other_headers,
    )
    assert duplicate_response.status_code == 409


@pytest.mark.integration
@pytest.mark.asyncio
async def test_owner_id_studio_filters_require_matching_authenticated_owner(client: AsyncClient):
    suffix = uuid4().hex[:8]
    owner_auth = await authenticate_via_otp(
        client,
        email=f"fr01-owner-filter-{suffix}@example.com",
        name="Owner Filter",
    )
    owner_headers = {"Authorization": f"Bearer {owner_auth['access_token']}"}
    other_headers = await _auth_headers(
        client,
        email=f"fr01-owner-filter-other-{suffix}@example.com",
    )
    studio = await _create_studio(
        client,
        owner_headers,
        name="Owner Filter Studio",
        slug=f"fr01-owner-filter-studio-{suffix}",
    )
    owner_id = owner_auth["user"]["id"]

    public_list = await client.get("/api/v1/studios", params={"owner_id": owner_id})
    public_count = await client.get("/api/v1/studios/count", params={"owner_id": owner_id})
    assert public_list.status_code == 401
    assert public_count.status_code == 401

    other_list = await client.get(
        "/api/v1/studios",
        params={"owner_id": owner_id},
        headers=other_headers,
    )
    other_count = await client.get(
        "/api/v1/studios/count",
        params={"owner_id": owner_id},
        headers=other_headers,
    )
    assert other_list.status_code == 403
    assert other_count.status_code == 403

    owner_list = await client.get(
        "/api/v1/studios",
        params={"owner_id": owner_id},
        headers=owner_headers,
    )
    owner_count = await client.get(
        "/api/v1/studios/count",
        params={"owner_id": owner_id},
        headers=owner_headers,
    )
    assert owner_list.status_code == 200
    assert [item["id"] for item in owner_list.json()] == [studio["id"]]
    assert owner_count.status_code == 200
    assert owner_count.json()["count"] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_studio_services_endpoint_is_owner_scoped(client: AsyncClient):
    suffix = uuid4().hex[:8]
    owner_headers = await _auth_headers(
        client,
        email=f"fr01-services-owner-{suffix}@example.com",
    )
    stranger_headers = await _auth_headers(
        client,
        email=f"fr01-services-stranger-{suffix}@example.com",
    )
    studio = await _create_studio(
        client,
        owner_headers,
        name="FR01 Services Studio",
        slug=f"fr01-services-studio-{suffix}",
    )
    active_service = await _create_course_service(
        client,
        owner_headers,
        studio_id=studio["id"],
        name="Active Course",
    )
    inactive_service = await _create_course_service(
        client,
        owner_headers,
        studio_id=studio["id"],
        name="Inactive Course",
    )
    delete_response = await client.delete(
        f"/api/v1/services/{inactive_service['id']}",
        headers=owner_headers,
    )
    assert delete_response.status_code == 200

    response = await client.get(
        f"/api/v1/studios/{studio['id']}/services",
        headers=owner_headers,
    )
    assert response.status_code == 200
    service_ids = {item["id"] for item in response.json()}
    assert service_ids == {active_service["id"], inactive_service["id"]}

    active_response = await client.get(
        f"/api/v1/studios/{studio['id']}/services",
        params={"is_active": True},
        headers=owner_headers,
    )
    assert active_response.status_code == 200
    assert [item["id"] for item in active_response.json()] == [active_service["id"]]

    forbidden_response = await client.get(
        f"/api/v1/studios/{studio['id']}/services",
        headers=stranger_headers,
    )
    assert forbidden_response.status_code == 403


@pytest.mark.integration
@pytest.mark.asyncio
async def test_orders_my_and_owner_orders_are_scoped(client: AsyncClient):
    suffix = uuid4().hex[:8]
    owner_headers = await _auth_headers(
        client,
        email=f"fr01-orders-owner-{suffix}@example.com",
    )
    stranger_headers = await _auth_headers(
        client,
        email=f"fr01-orders-stranger-{suffix}@example.com",
    )
    guest_email = f"fr01-order-guest-{suffix}@example.com"
    studio = await _create_studio(
        client,
        owner_headers,
        name="FR01 Orders Studio",
        slug=f"fr01-orders-studio-{suffix}",
    )
    service = await _create_course_service(
        client,
        owner_headers,
        studio_id=studio["id"],
    )
    await _create_occurrence(
        client,
        owner_headers,
        studio_id=studio["id"],
        service_id=service["id"],
        starts_in_days=2,
    )
    await _create_occurrence(
        client,
        owner_headers,
        studio_id=studio["id"],
        service_id=service["id"],
        starts_in_days=9,
    )

    booking_response = await client.post(
        "/api/v1/bookings",
        json={
            "service_id": service["id"],
            "guest_name": "Order Guest",
            "guest_email": guest_email,
            "guest_phone": "+353870000000",
        },
    )
    assert booking_response.status_code == 201, booking_response.text
    created_order = booking_response.json()["order"]

    guest_auth = await authenticate_via_otp(client, email=guest_email, name="Order Guest")
    guest_headers = {"Authorization": f"Bearer {guest_auth['access_token']}"}
    my_orders_response = await client.get("/api/v1/orders/my", headers=guest_headers)
    assert my_orders_response.status_code == 200
    my_orders = my_orders_response.json()
    assert [order["id"] for order in my_orders] == [created_order["id"]]
    assert my_orders[0]["user_id"] == guest_auth["user"]["id"]
    assert my_orders[0]["service"]["id"] == service["id"]
    assert {booking["id"] for booking in my_orders[0]["bookings"]} == {
        booking["id"] for booking in booking_response.json()["bookings"]
    }

    missing_studio_response = await client.get("/api/v1/orders", headers=owner_headers)
    assert missing_studio_response.status_code == 400
    assert missing_studio_response.json()["detail"] == "studio_id is required"

    owner_orders_response = await client.get(
        "/api/v1/orders",
        params={"studio_id": studio["id"]},
        headers=owner_headers,
    )
    assert owner_orders_response.status_code == 200
    assert [order["id"] for order in owner_orders_response.json()] == [created_order["id"]]

    stranger_orders_response = await client.get(
        "/api/v1/orders",
        params={"studio_id": studio["id"]},
        headers=stranger_headers,
    )
    assert stranger_orders_response.status_code == 403
