"""Integration tests for studio RBAC and frontend role contracts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from tests.conftest import authenticate_via_otp

from app.core.uow_factory import uow_scope
from app.models import Booking, BookingStatus, StudioMember, StudioMemberRole


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
    instructor_id: int | None = None,
) -> int:
    start_time = datetime.now(UTC) + timedelta(days=7)
    payload = {
        "studio_id": studio_id,
        "service_id": service_id,
        "start_time": start_time.isoformat(),
        "end_time": (start_time + timedelta(hours=1)).isoformat(),
        "title": "RBAC Session",
        "max_capacity": 10,
        "price_cents": 1500,
    }
    if instructor_id is not None:
        payload["instructor_id"] = instructor_id
    response = await client.post(
        "/api/v1/occurrences",
        json=payload,
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
) -> int:
    async with uow_scope(session=app_with_rollback_uow.state._integration_session) as uow:
        member = await uow.studio_members.add(
            StudioMember(
                studio_id=studio_id,
                user_id=user_id,
                role=role.value,
            )
        )
        return member.id


async def _create_booking(client: AsyncClient, *, occurrence_id: int, email: str) -> int:
    response = await client.post(
        "/api/v1/bookings",
        json={
            "occurrence_id": occurrence_id,
            "guest_name": "Attendance Guest",
            "guest_email": email,
            "guest_phone": "+111111111",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _set_booking_status(
    app_with_rollback_uow,
    *,
    booking_id: int,
    status: str,
) -> None:
    async with uow_scope(session=app_with_rollback_uow.state._integration_session) as uow:
        result = await uow.session.execute(select(Booking).where(Booking.id == booking_id))
        booking = result.scalar_one()
        booking.status = status
        booking.reserved_until = None


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
    my_studios = my_studios_response.json()["items"]
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
async def test_instructor_can_view_booking_but_cannot_cancel(
    client: AsyncClient,
    app_with_rollback_uow,
) -> None:
    """view_bookings must not imply cancel; manage_bookings is required for staff."""
    owner_headers, _owner = await _authenticate(
        client,
        email="fr02-cancel-owner@example.com",
        name="Cancel Owner",
    )
    instructor_headers, instructor = await _authenticate(
        client,
        email="fr02-cancel-instructor@example.com",
        name="Cancel Instructor",
    )
    manager_headers, manager = await _authenticate(
        client,
        email="fr02-cancel-manager@example.com",
        name="Cancel Manager",
    )
    studio_id = await _create_studio(client, owner_headers, name="Cancel RBAC Studio")
    service_id = await _create_service(client, owner_headers, studio_id=studio_id)
    occurrence_id = await _create_occurrence(
        client,
        owner_headers,
        studio_id=studio_id,
        service_id=service_id,
    )
    booking_id = await _create_booking(
        client,
        occurrence_id=occurrence_id,
        email="cancel-rbac-guest@example.com",
    )
    await _add_studio_member(
        app_with_rollback_uow,
        studio_id=studio_id,
        user_id=instructor["id"],
        role=StudioMemberRole.INSTRUCTOR,
    )
    await _add_studio_member(
        app_with_rollback_uow,
        studio_id=studio_id,
        user_id=manager["id"],
        role=StudioMemberRole.MANAGER,
    )

    view_response = await client.get(
        f"/api/v1/bookings/{booking_id}",
        headers=instructor_headers,
    )
    assert view_response.status_code == 200, view_response.text

    instructor_cancel = await client.patch(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=instructor_headers,
    )
    assert instructor_cancel.status_code == 403

    manager_cancel = await client.patch(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=manager_headers,
    )
    assert manager_cancel.status_code == 200, manager_cancel.text
    assert manager_cancel.json()["status"] == "cancelled"


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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_owner_assigns_instructor_to_occurrence(
    client: AsyncClient,
    app_with_rollback_uow,
) -> None:
    owner_headers, _owner = await _authenticate(
        client,
        email="fr03-assign-owner@example.com",
        name="FR03 Owner",
    )
    instructor_headers, instructor = await _authenticate(
        client,
        email="fr03-assign-instructor@example.com",
        name="FR03 Instructor",
    )
    studio_id = await _create_studio(client, owner_headers, name="FR03 Assign Studio")
    service_id = await _create_service(client, owner_headers, studio_id=studio_id)
    occurrence_id = await _create_occurrence(
        client,
        owner_headers,
        studio_id=studio_id,
        service_id=service_id,
    )
    instructor_member_id = await _add_studio_member(
        app_with_rollback_uow,
        studio_id=studio_id,
        user_id=instructor["id"],
        role=StudioMemberRole.INSTRUCTOR,
    )

    response = await client.patch(
        f"/api/v1/occurrences/{occurrence_id}",
        json={"instructor_id": instructor_member_id},
        headers=owner_headers,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["instructor_id"] == instructor_member_id
    assert payload["instructor"] == {
        "studio_member_id": instructor_member_id,
        "user_id": instructor["id"],
        "name": "FR03 Instructor",
        "role": "instructor",
    }

    mine_response = await client.get(
        f"/api/v1/occurrences/mine?studio_id={studio_id}",
        headers=instructor_headers,
    )
    assert mine_response.status_code == 200, mine_response.text
    assert [occurrence["id"] for occurrence in mine_response.json()["items"]] == [occurrence_id]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_instructor_mine_endpoint_only_returns_assigned_occurrences(
    client: AsyncClient,
    app_with_rollback_uow,
) -> None:
    owner_headers, _owner = await _authenticate(
        client,
        email="fr03-mine-owner@example.com",
        name="FR03 Owner",
    )
    first_headers, first_instructor = await _authenticate(
        client,
        email="fr03-mine-first@example.com",
        name="FR03 First Instructor",
    )
    _second_headers, second_instructor = await _authenticate(
        client,
        email="fr03-mine-second@example.com",
        name="FR03 Second Instructor",
    )
    studio_id = await _create_studio(client, owner_headers, name="FR03 Mine Studio")
    service_id = await _create_service(client, owner_headers, studio_id=studio_id)
    first_member_id = await _add_studio_member(
        app_with_rollback_uow,
        studio_id=studio_id,
        user_id=first_instructor["id"],
        role=StudioMemberRole.INSTRUCTOR,
    )
    second_member_id = await _add_studio_member(
        app_with_rollback_uow,
        studio_id=studio_id,
        user_id=second_instructor["id"],
        role=StudioMemberRole.INSTRUCTOR,
    )
    first_occurrence_id = await _create_occurrence(
        client,
        owner_headers,
        studio_id=studio_id,
        service_id=service_id,
        instructor_id=first_member_id,
    )
    await _create_occurrence(
        client,
        owner_headers,
        studio_id=studio_id,
        service_id=service_id,
        instructor_id=second_member_id,
    )

    response = await client.get(
        f"/api/v1/occurrences/mine?studio_id={studio_id}",
        headers=first_headers,
    )

    assert response.status_code == 200, response.text
    occurrences = response.json()["items"]
    assert [occurrence["id"] for occurrence in occurrences] == [first_occurrence_id]
    assert occurrences[0]["instructor"]["user_id"] == first_instructor["id"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_attendance_actions_are_idempotent_and_permission_checked(
    client: AsyncClient,
    app_with_rollback_uow,
) -> None:
    owner_headers, _owner = await _authenticate(
        client,
        email="fr03-attendance-owner@example.com",
        name="FR03 Owner",
    )
    instructor_headers, instructor = await _authenticate(
        client,
        email="fr03-attendance-instructor@example.com",
        name="FR03 Instructor",
    )
    other_headers, other_instructor = await _authenticate(
        client,
        email="fr03-attendance-other@example.com",
        name="FR03 Other Instructor",
    )
    studio_id = await _create_studio(client, owner_headers, name="FR03 Attendance Studio")
    service_id = await _create_service(client, owner_headers, studio_id=studio_id)
    instructor_member_id = await _add_studio_member(
        app_with_rollback_uow,
        studio_id=studio_id,
        user_id=instructor["id"],
        role=StudioMemberRole.INSTRUCTOR,
    )
    await _add_studio_member(
        app_with_rollback_uow,
        studio_id=studio_id,
        user_id=other_instructor["id"],
        role=StudioMemberRole.INSTRUCTOR,
    )
    occurrence_id = await _create_occurrence(
        client,
        owner_headers,
        studio_id=studio_id,
        service_id=service_id,
        instructor_id=instructor_member_id,
    )

    check_in_booking_id = await _create_booking(
        client,
        occurrence_id=occurrence_id,
        email="fr03-check-in@example.com",
    )
    no_show_booking_id = await _create_booking(
        client,
        occurrence_id=occurrence_id,
        email="fr03-no-show@example.com",
    )
    cancelled_booking_id = await _create_booking(
        client,
        occurrence_id=occurrence_id,
        email="fr03-cancelled@example.com",
    )
    await _set_booking_status(
        app_with_rollback_uow,
        booking_id=check_in_booking_id,
        status=BookingStatus.CONFIRMED,
    )
    await _set_booking_status(
        app_with_rollback_uow,
        booking_id=no_show_booking_id,
        status=BookingStatus.CONFIRMED,
    )
    await _set_booking_status(
        app_with_rollback_uow,
        booking_id=cancelled_booking_id,
        status=BookingStatus.CANCELLED,
    )

    forbidden_response = await client.patch(
        f"/api/v1/bookings/{check_in_booking_id}/check-in",
        headers=other_headers,
    )
    assert forbidden_response.status_code == 403

    first_check_in = await client.patch(
        f"/api/v1/bookings/{check_in_booking_id}/check-in",
        headers=instructor_headers,
    )
    second_check_in = await client.patch(
        f"/api/v1/bookings/{check_in_booking_id}/check-in",
        headers=instructor_headers,
    )
    assert first_check_in.status_code == 200, first_check_in.text
    assert second_check_in.status_code == 200, second_check_in.text
    assert first_check_in.json()["status"] == BookingStatus.COMPLETED
    assert first_check_in.json()["checked_in_at"] == second_check_in.json()["checked_in_at"]

    no_show_after_check_in = await client.patch(
        f"/api/v1/bookings/{check_in_booking_id}/mark-no-show",
        headers=owner_headers,
    )
    assert no_show_after_check_in.status_code == 400

    first_no_show = await client.patch(
        f"/api/v1/bookings/{no_show_booking_id}/mark-no-show",
        headers=owner_headers,
    )
    second_no_show = await client.patch(
        f"/api/v1/bookings/{no_show_booking_id}/mark-no-show",
        headers=owner_headers,
    )
    assert first_no_show.status_code == 200, first_no_show.text
    assert second_no_show.status_code == 200, second_no_show.text
    assert first_no_show.json()["status"] == BookingStatus.NO_SHOW
    assert first_no_show.json()["no_show_at"] == second_no_show.json()["no_show_at"]

    cancel_no_show = await client.patch(
        f"/api/v1/bookings/{no_show_booking_id}/cancel",
        headers=owner_headers,
    )
    assert cancel_no_show.status_code == 400

    cancelled_check_in = await client.patch(
        f"/api/v1/bookings/{cancelled_booking_id}/check-in",
        headers=owner_headers,
    )
    assert cancelled_check_in.status_code == 400
