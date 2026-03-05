"""
Интеграционные тесты API студий, слотов и бронирований.

Проверяем, что end-to-end сценарии записи в БД работают корректно
поверх текущей UoW-транзакционной модели.
"""
from datetime import datetime, timedelta
import re
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """HTTP-клиент для тестов API (использует реальное приложение и БД)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


async def _authenticate_user(client: AsyncClient, email: str = "owner@example.com"):
    """
    Создаёт пользователя через Magic Link и возвращает access/refresh токены и данные пользователя.
    """
    captured_url: list[str] = []

    async def capture_email(to: str, url: str) -> None:
        captured_url.append(url)

    with patch("app.services.auth.send_magic_link_email", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = capture_email
        r1 = await client.post(
            "/api/v1/auth/magic-link/request",
            json={"email": email, "name": "Owner User"},
        )

    assert r1.status_code == 200
    assert len(captured_url) == 1

    match = re.search(r"token=([^&]+)", captured_url[0])
    assert match is not None
    token = match.group(1)

    r2 = await client.get("/api/v1/auth/magic-link/verify", params={"token": token})
    assert r2.status_code == 200
    data = r2.json()
    return data["access_token"], data["refresh_token"], data["user"]


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
    access, _refresh, user = await _authenticate_user(client)
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
    access, _refresh, user = await _authenticate_user(client, email="slot-owner@example.com")
    headers = {"Authorization": f"Bearer {access}"}

    # Создаём студию, к которой будет привязан слот
    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "Slot Studio",
            "description": "For slots",
            "email": "slot-studio@example.com",
            "address": "Slot street 1",
        },
        headers=headers,
    )
    assert r_studio.status_code == 201
    studio_id = r_studio.json()["id"]
    assert r_studio.json()["owner_id"] == user["id"]

    # Создаём слот в будущем
    start = datetime.utcnow() + timedelta(hours=2)
    end = start + timedelta(hours=1)
    r_slot = await client.post(
        "/api/v1/slots",
        json={
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "title": "Morning Class",
            "description": "Test slot",
            "max_capacity": 5,
            "price_cents": 1000,
            "studio_id": studio_id,
            "service_id": None,
        },
        headers=headers,
    )
    assert r_slot.status_code == 201
    slot = r_slot.json()
    slot_id = slot["id"]
    assert slot["studio_id"] == studio_id

    # Гостевое бронирование этого слота
    r_booking = await client.post(
        "/api/v1/bookings",
        json={
            "slot_id": slot_id,
            "guest_name": "Guest User",
            "guest_email": "guest@example.com",
            "guest_phone": "+111111111",
        },
    )
    assert r_booking.status_code == 201
    booking = r_booking.json()
    booking_id = booking["id"]
    assert booking["slot_id"] == slot_id
    assert booking["status"] == "pending"

    # Отмена бронирования
    r_cancel = await client.patch(f"/api/v1/bookings/{booking_id}/cancel")
    assert r_cancel.status_code == 200
    cancelled = r_cancel.json()
    assert cancelled["id"] == booking_id
    assert cancelled["status"] == "cancelled"

    # Удаляем слот
    r_delete_slot = await client.delete(f"/api/v1/slots/{slot_id}", headers=headers)
    assert r_delete_slot.status_code == 204

    # Слот больше не существует
    r_get_slot = await client.get(f"/api/v1/slots/{slot_id}")
    assert r_get_slot.status_code == 404

