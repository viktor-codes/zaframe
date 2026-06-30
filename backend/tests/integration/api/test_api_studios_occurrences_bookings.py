"""
Интеграционные тесты API студий, слотов и бронирований.

Проверяем, что end-to-end сценарии записи в БД работают корректно
поверх текущей UoW-транзакционной модели.
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from tests.conftest import authenticate_via_otp, create_test_service


async def _authenticate_user(client: AsyncClient, email: str = "owner@example.com"):
    """Create user via OTP; return access token and user (refresh is httpOnly cookie)."""
    data = await authenticate_via_otp(client, email=email, name="Owner User")
    assert "refresh_token" not in data
    return data["access_token"], data["user"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_studio_crud_flow(client: AsyncClient):
    """
    Полный CRUD-флоу для студии:
    - создаём владельца через Magic Link
    - создаём студию
    - обновляем студию
    - удаляем студию и убеждаемся, что она больше не доступна.
    """
    access, user = await _authenticate_user(client)
    headers = {"Authorization": f"Bearer {access}"}

    # Создание студии
    r_create = await client.post(
        "/api/v1/studios",
        json={
            "name": "Test Studio",
            "description": "Test description",
            "email": "studio@example.com",
            "phone": "+123456789",
            "address": "Test street 1",
            "timezone": "Europe/Dublin",
        },
        headers=headers,
    )
    assert r_create.status_code == 201
    studio = r_create.json()
    assert studio["name"] == "Test Studio"
    assert studio["owner_id"] == user["id"]
    studio_id = studio["id"]

    # Обновление студии
    r_update = await client.patch(
        f"/api/v1/studios/{studio_id}",
        json={"name": "Updated Studio"},
        headers=headers,
    )
    assert r_update.status_code == 200
    updated = r_update.json()
    assert updated["name"] == "Updated Studio"

    # Удаление студии
    r_delete = await client.delete(f"/api/v1/studios/{studio_id}", headers=headers)
    assert r_delete.status_code == 204

    # Студия больше не существует
    r_get = await client.get(f"/api/v1/studios/{studio_id}")
    assert r_get.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_slot_and_booking_flow(client: AsyncClient):
    """
    Флоу для слота и бронирования:
    - создаём владельца и студию
    - создаём слот
    - создаём гостевое бронирование слота
    - отменяем бронирование
    - удаляем слот и убеждаемся, что он недоступен.
    """
    access, user = await _authenticate_user(client, email="slot-owner@example.com")
    headers = {"Authorization": f"Bearer {access}"}

    # Создаём студию, к которой будет привязан слот
    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "Occurrence Studio",
            "description": "For slots",
            "email": "slot-studio@example.com",
            "address": "Occurrence street 1",
            "timezone": "Europe/Dublin",
            "cancel_before_hours": 0,
        },
        headers=headers,
    )
    assert r_studio.status_code == 201
    studio_id = r_studio.json()["id"]
    assert r_studio.json()["owner_id"] == user["id"]
    service_id = await create_test_service(
        client,
        headers=headers,
        studio_id=studio_id,
        name="Morning Class",
        max_capacity=5,
        price_single_cents=1000,
    )

    # Создаём слот в будущем
    start = datetime.now(UTC) + timedelta(hours=2)
    end = start + timedelta(hours=1)
    r_occurrence = await client.post(
        "/api/v1/occurrences",
        json={
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "title": "Morning Class",
            "description": "Test slot",
            "max_capacity": 5,
            "price_cents": 1000,
            "studio_id": studio_id,
            "service_id": service_id,
        },
        headers=headers,
    )
    assert r_occurrence.status_code == 201
    occurrence = r_occurrence.json()
    occurrence_id = occurrence["id"]
    assert occurrence["studio_id"] == studio_id

    public_occurrences = await client.get(
        "/api/v1/occurrences",
        params={"studio_id": studio_id},
    )
    assert public_occurrences.status_code == 401

    missing_studio_filter = await client.get("/api/v1/occurrences", headers=headers)
    assert missing_studio_filter.status_code == 400
    assert missing_studio_filter.json()["detail"] == "studio_id is required"

    owner_occurrences = await client.get(
        "/api/v1/occurrences",
        params={"studio_id": studio_id},
        headers=headers,
    )
    assert owner_occurrences.status_code == 200
    assert [item["id"] for item in owner_occurrences.json()] == [occurrence_id]

    owner_count = await client.get(
        "/api/v1/occurrences/count",
        params={"studio_id": studio_id},
        headers=headers,
    )
    assert owner_count.status_code == 200
    assert owner_count.json()["count"] == 1

    public_nested = await client.get(f"/api/v1/studios/{studio_id}/occurrences")
    assert public_nested.status_code == 401

    stranger_access, _ = await _authenticate_user(client, email="slot-stranger@example.com")
    stranger_headers = {"Authorization": f"Bearer {stranger_access}"}
    stranger_occurrences = await client.get(
        "/api/v1/occurrences",
        params={"studio_id": studio_id},
        headers=stranger_headers,
    )
    assert stranger_occurrences.status_code == 403

    # Гостевое бронирование этого слота
    r_booking = await client.post(
        "/api/v1/bookings",
        json={
            "occurrence_id": occurrence_id,
            "guest_name": "Guest User",
            "guest_email": "guest@example.com",
            "guest_phone": "+111111111",
        },
    )
    assert r_booking.status_code == 201
    booking = r_booking.json()
    booking_id = booking["id"]
    assert booking["occurrence_id"] == occurrence_id
    assert booking["status"] == "pending"

    # Отмена бронирования (только гость, совпадающий по email)
    guest_access, _ = await _authenticate_user(client, email="guest@example.com")
    guest_headers = {"Authorization": f"Bearer {guest_access}"}
    r_cancel = await client.patch(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=guest_headers,
    )
    assert r_cancel.status_code == 200
    cancelled = r_cancel.json()
    assert cancelled["id"] == booking_id
    assert cancelled["status"] == "cancelled"

    # Удаляем слот
    r_delete_occurrence = await client.delete(
        f"/api/v1/occurrences/{occurrence_id}", headers=headers
    )
    assert r_delete_occurrence.status_code == 204

    # Слот сохраняется как cancelled, чтобы история бронирований не пропала
    r_get_occurrence = await client.get(f"/api/v1/occurrences/{occurrence_id}")
    assert r_get_occurrence.status_code == 200
    assert r_get_occurrence.json()["status"] == "cancelled"
