"""Integration tests for studio RBAC and frontend role contracts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from tests.conftest import authenticate_via_otp

from app.core.uow_factory import uow_scope
from app.models import StudioMember, StudioMemberRole


async def _authenticate(
    client: AsyncClient,
    *,
    email: str,
    name: str,
) -> tuple[dict[str, str], dict]:
    data = await authenticate_via_otp(client, email=email, name=name)
    return {"Authorization": f"Bearer {data['access_token']}"}, data["user"]


async def _create_studio(client: AsyncClient, headers: dict[str, str], *, name: str) -> int:
    response = await client.post(
        "/api/v1/studios",
        json={
            "name": name,
            "email": "rbac-studio@example.com",
            "timezone": "Europe/Dublin",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_service(client: AsyncClient, headers: dict[str, str], *, studio_id: int) -> int:
    response = await client.post(
        "/api/v1/services",
        json={
            "studio_id": studio_id,
            "name": "RBAC Yoga",
            "type": "single",
            "duration_minutes": 60,
            "max_capacity": 10,
            "price_single_cents": 1500,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_occurrence(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    studio_id: int,
    service_id: int,
) -> int:
    start_time = datetime.now(UTC) + timedelta(days=7)
    response = await client.post(
        "/api/v1/occurrences",
        json={
            "studio_id": studio_id,
            "service_id": service_id,
            "start_time": start_time.isoformat(),
            "end_time": (start_time + timedelta(hours=1)).isoformat(),
            "title": "RBAC Session",
            "max_capacity": 10,
            "price_cents": 1500,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _add_studio_member(
    app_with_rollback_uow,
    *,
    studio_id: int,
    user_id: int,
    role: StudioMemberRole,
) -> None:
    async with uow_scope(session=app_with_rollback_uow.state._integration_session) as uow:
        await uow.studio_members.add(
            StudioMember(
                studio_id=studio_id,
                user_id=user_id,
                role=role.value,
            )
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_studio_creator_gets_owner_membership_and_roles_contract(
    client: AsyncClient,
) -> None:
    owner_headers, _owner = await _authenticate(
        client,
        email="fr02-owner@example.com",
        name="FR02 Owner",
    )
    studio_id = await _create_studio(client, owner_headers, name="Owner RBAC Studio")

    me_response = await client.get("/api/v1/auth/me", headers=owner_headers)
    assert me_response.status_code == 200, me_response.text
    me = me_response.json()
    assert me["role"] == "studio_owner"
    assert {"studio_id": studio_id, "role": "owner"} in me["roles"]

    my_studios_response = await client.get("/api/v1/studios/my", headers=owner_headers)
    assert my_studios_response.status_code == 200, my_studios_response.text
    my_studios = my_studios_response.json()
    assert my_studios[0]["id"] == studio_id
    assert my_studios[0]["role"] == "owner"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_manager_can_manage_operational_areas_but_not_studio_settings(
    client: AsyncClient,
    app_with_rollback_uow,
) -> None:
    owner_headers, _owner = await _authenticate(
        client,
        email="fr02-manager-owner@example.com",
        name="FR02 Owner",
    )
    manager_headers, manager = await _authenticate(
        client,
        email="fr02-manager@example.com",
        name="FR02 Manager",
    )
    studio_id = await _create_studio(client, owner_headers, name="Manager RBAC Studio")
    await _add_studio_member(
        app_with_rollback_uow,
        studio_id=studio_id,
        user_id=manager["id"],
        role=StudioMemberRole.MANAGER,
    )

    service_id = await _create_service(client, manager_headers, studio_id=studio_id)
    occurrence_id = await _create_occurrence(
        client,
        manager_headers,
        studio_id=studio_id,
        service_id=service_id,
    )

    settings_response = await client.patch(
        f"/api/v1/studios/{studio_id}",
        json={"name": "Manager Should Not Rename"},
        headers=manager_headers,
    )
    assert settings_response.status_code == 403

    bookings_response = await client.get(
        f"/api/v1/occurrences/{occurrence_id}/bookings",
        headers=manager_headers,
    )
    assert bookings_response.status_code == 200, bookings_response.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_instructor_can_view_bookings_but_cannot_manage_studio_or_schedule(
    client: AsyncClient,
    app_with_rollback_uow,
) -> None:
    owner_headers, _owner = await _authenticate(
        client,
        email="fr02-instructor-owner@example.com",
        name="FR02 Owner",
    )
    instructor_headers, instructor = await _authenticate(
        client,
        email="fr02-instructor@example.com",
        name="FR02 Instructor",
    )
    studio_id = await _create_studio(client, owner_headers, name="Instructor RBAC Studio")
    service_id = await _create_service(client, owner_headers, studio_id=studio_id)
    occurrence_id = await _create_occurrence(
        client,
        owner_headers,
        studio_id=studio_id,
        service_id=service_id,
    )
    await _add_studio_member(
        app_with_rollback_uow,
        studio_id=studio_id,
        user_id=instructor["id"],
        role=StudioMemberRole.INSTRUCTOR,
    )

    bookings_response = await client.get(
        f"/api/v1/occurrences/{occurrence_id}/bookings",
        headers=instructor_headers,
    )
    assert bookings_response.status_code == 200, bookings_response.text

    settings_response = await client.patch(
        f"/api/v1/studios/{studio_id}",
        json={"name": "Instructor Should Not Rename"},
        headers=instructor_headers,
    )
    assert settings_response.status_code == 403

    schedule_response = await client.post(
        "/api/v1/occurrences",
        json={
            "studio_id": studio_id,
            "service_id": service_id,
            "start_time": (datetime.now(UTC) + timedelta(days=8)).isoformat(),
            "end_time": (datetime.now(UTC) + timedelta(days=8, hours=1)).isoformat(),
            "title": "Instructor Should Not Create",
            "max_capacity": 10,
            "price_cents": 1500,
        },
        headers=instructor_headers,
    )
    assert schedule_response.status_code == 403


@pytest.mark.integration
@pytest.mark.asyncio
async def test_non_member_cannot_access_studio_dashboard_endpoints(
    client: AsyncClient,
) -> None:
    owner_headers, _owner = await _authenticate(
        client,
        email="fr02-non-member-owner@example.com",
        name="FR02 Owner",
    )
    stranger_headers, _stranger = await _authenticate(
        client,
        email="fr02-stranger@example.com",
        name="FR02 Stranger",
    )
    studio_id = await _create_studio(client, owner_headers, name="Non Member RBAC Studio")

    response = await client.post(
        "/api/v1/services",
        json={
            "studio_id": studio_id,
            "name": "Forbidden Service",
            "type": "single",
            "duration_minutes": 60,
            "max_capacity": 10,
            "price_single_cents": 1500,
        },
        headers=stranger_headers,
    )
    assert response.status_code == 403
