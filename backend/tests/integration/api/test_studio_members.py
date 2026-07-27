"""Integration tests for studio members management API."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from tests.conftest import authenticate_via_otp


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
            "email": "members-studio@example.com",
            "timezone": "Europe/Dublin",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_owner_lists_adds_updates_and_removes_member(client: AsyncClient) -> None:
    owner_headers, _owner = await _authenticate(
        client,
        email="members-owner@example.com",
        name="Members Owner",
    )
    _invitee_headers, invitee = await _authenticate(
        client,
        email="members-invitee@example.com",
        name="Members Invitee",
    )
    studio_id = await _create_studio(client, owner_headers, name="Members Happy Path Studio")

    list_before = await client.get(
        f"/api/v1/studios/{studio_id}/members",
        headers=owner_headers,
    )
    assert list_before.status_code == 200, list_before.text
    assert list_before.json()["total"] == 1
    assert list_before.json()["items"][0]["role"] == "owner"

    create_response = await client.post(
        f"/api/v1/studios/{studio_id}/members",
        json={"email": "members-invitee@example.com", "role": "instructor"},
        headers=owner_headers,
    )
    assert create_response.status_code == 201, create_response.text
    member = create_response.json()
    assert member["user_id"] == invitee["id"]
    assert member["role"] == "instructor"
    assert member["email"] == "members-invitee@example.com"
    member_id = member["id"]

    patch_response = await client.patch(
        f"/api/v1/studios/{studio_id}/members/{member_id}",
        json={"role": "manager"},
        headers=owner_headers,
    )
    assert patch_response.status_code == 200, patch_response.text
    assert patch_response.json()["role"] == "manager"

    delete_response = await client.delete(
        f"/api/v1/studios/{studio_id}/members/{member_id}",
        headers=owner_headers,
    )
    assert delete_response.status_code == 204, delete_response.text

    list_after = await client.get(
        f"/api/v1/studios/{studio_id}/members",
        headers=owner_headers,
    )
    assert list_after.status_code == 200, list_after.text
    assert list_after.json()["total"] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unauthenticated_members_request_returns_401(client: AsyncClient) -> None:
    owner_headers, _owner = await _authenticate(
        client,
        email="members-401-owner@example.com",
        name="Members 401 Owner",
    )
    studio_id = await _create_studio(client, owner_headers, name="Members 401 Studio")

    response = await client.get(f"/api/v1/studios/{studio_id}/members")
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_manager_and_instructor_cannot_manage_members(client: AsyncClient) -> None:
    owner_headers, _owner = await _authenticate(
        client,
        email="members-403-owner@example.com",
        name="Members 403 Owner",
    )
    manager_headers, _manager = await _authenticate(
        client,
        email="members-403-manager@example.com",
        name="Members 403 Manager",
    )
    instructor_headers, _instructor = await _authenticate(
        client,
        email="members-403-instructor@example.com",
        name="Members 403 Instructor",
    )
    studio_id = await _create_studio(client, owner_headers, name="Members 403 Studio")

    add_manager = await client.post(
        f"/api/v1/studios/{studio_id}/members",
        json={"email": "members-403-manager@example.com", "role": "manager"},
        headers=owner_headers,
    )
    assert add_manager.status_code == 201, add_manager.text
    add_instructor = await client.post(
        f"/api/v1/studios/{studio_id}/members",
        json={"email": "members-403-instructor@example.com", "role": "instructor"},
        headers=owner_headers,
    )
    assert add_instructor.status_code == 201, add_instructor.text

    manager_list = await client.get(
        f"/api/v1/studios/{studio_id}/members",
        headers=manager_headers,
    )
    assert manager_list.status_code == 403

    instructor_add = await client.post(
        f"/api/v1/studios/{studio_id}/members",
        json={"email": "someone@example.com", "role": "instructor"},
        headers=instructor_headers,
    )
    assert instructor_add.status_code == 403


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cannot_remove_or_demote_last_owner(client: AsyncClient) -> None:
    owner_headers, _owner = await _authenticate(
        client,
        email="members-last-owner@example.com",
        name="Members Last Owner",
    )
    studio_id = await _create_studio(client, owner_headers, name="Members Last Owner Studio")

    list_response = await client.get(
        f"/api/v1/studios/{studio_id}/members",
        headers=owner_headers,
    )
    assert list_response.status_code == 200, list_response.text
    owner_member_id = list_response.json()["items"][0]["id"]

    demote = await client.patch(
        f"/api/v1/studios/{studio_id}/members/{owner_member_id}",
        json={"role": "manager"},
        headers=owner_headers,
    )
    assert demote.status_code == 409

    remove = await client.delete(
        f"/api/v1/studios/{studio_id}/members/{owner_member_id}",
        headers=owner_headers,
    )
    assert remove.status_code == 409


@pytest.mark.integration
@pytest.mark.asyncio
async def test_duplicate_member_returns_409(client: AsyncClient) -> None:
    owner_headers, _owner = await _authenticate(
        client,
        email="members-dup-owner@example.com",
        name="Members Dup Owner",
    )
    _invitee_headers, _invitee = await _authenticate(
        client,
        email="members-dup-invitee@example.com",
        name="Members Dup Invitee",
    )
    studio_id = await _create_studio(client, owner_headers, name="Members Dup Studio")

    first = await client.post(
        f"/api/v1/studios/{studio_id}/members",
        json={"email": "members-dup-invitee@example.com", "role": "manager"},
        headers=owner_headers,
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        f"/api/v1/studios/{studio_id}/members",
        json={"email": "members-dup-invitee@example.com", "role": "instructor"},
        headers=owner_headers,
    )
    assert second.status_code == 409


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unknown_email_returns_404(client: AsyncClient) -> None:
    owner_headers, _owner = await _authenticate(
        client,
        email="members-unknown-owner@example.com",
        name="Members Unknown Owner",
    )
    studio_id = await _create_studio(client, owner_headers, name="Members Unknown Studio")

    response = await client.post(
        f"/api/v1/studios/{studio_id}/members",
        json={"email": "no-such-user@example.com", "role": "instructor"},
        headers=owner_headers,
    )
    assert response.status_code == 404
