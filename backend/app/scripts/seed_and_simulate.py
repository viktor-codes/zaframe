"""
Утилита для сидирования демо-данных и имитации нагрузки.

Цели:
- создать N студий, у каждой по несколько услуг
- сгенерировать расписание курсов на несколько недель
- симулировать сотню "пользователей", которые случайно бронируют
  одиночные занятия и курсы, проверяя надёжность бизнес-логики

Запуск (из директории backend):
    uv run python -m app.scripts.seed_and_simulate
или:
    python -m app.scripts.seed_and_simulate
"""
from __future__ import annotations

import asyncio
import random
from datetime import date, time, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models.service import ServiceType, Service
from app.models.slot import Slot
from app.models.user import User
from app.schemas.booking import BookingCreate
from app.schemas.service import CourseBookingCreate, ServiceCreate
from app.schemas.studio import StudioCreate
from app.services.booking import create_booking
from app.services.service import (
    create_course_booking,
    create_service,
    occurrence_generator,
)
from app.services.studio import create_studio


async def _create_owner(db: AsyncSession, idx: int) -> User:
    """Создать владельца студий для демо."""
    user = User(
        email=f"owner{idx}@example.com",
        name=f"Owner {idx}",
        phone=None,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def seed_demo_data(
    db: AsyncSession,
    *,
    studios_count: int = 10,
    min_services: int = 3,
    max_services: int = 5,
    weeks_count: int = 6,
) -> None:
    """
    Сидирует базу тестовыми студиями, услугами и расписанием.
    """
    random.seed(42)

    start_date = date.today() + timedelta(days=7)  # чтобы слоты точно были в будущем

    for i in range(studios_count):
        owner = await _create_owner(db, i)
        studio_schema = StudioCreate(
            name=f"Demo Studio {i + 1}",
            description="Demo studio for load testing",
            email=f"studio{i + 1}@example.com",
            phone=None,
            address="Demo Address",
            owner_id=owner.id,
        )
        studio = await create_studio(db, studio_schema)

        services_in_studio = random.randint(min_services, max_services)
        for j in range(services_in_studio):
            is_course = random.choice([True, False])
            service_type = ServiceType.COURSE if is_course else ServiceType.SINGLE_CLASS
            duration = random.choice([45, 60, 90])
            max_capacity = random.choice([8, 10, 12, 15])
            price_single = random.choice([1200, 1500, 1800])
            price_course = (
                price_single * weeks_count
                if is_course
                else None
            )

            service_schema = ServiceCreate(
                studio_id=studio.id,
                name=f"Service {j + 1} of {studio.name}",
                description=f"Auto-generated {service_type}",
                type=service_type,
                duration_minutes=duration,
                max_capacity=max_capacity,
                price_single_cents=price_single,
                price_course_cents=price_course,
                soft_limit_ratio=1.0 if not is_course else 1.2,
                hard_limit_ratio=1.5,
                max_overbooked_ratio=0.0 if not is_course else 0.3,
            )
            service = await create_service(
                db,
                studio_id=studio.id,
                data=service_schema.model_dump(exclude={"studio_id"}),
            )

            # Для курсов генерируем расписание на weeks_count недель
            if service.type == ServiceType.COURSE:
                await occurrence_generator(
                    db,
                    studio_id=studio.id,
                    service_id=service.id,
                    days=[1, 3],  # вторник и четверг, условно
                    start_time=time(18, 0),
                    weeks_count=weeks_count,
                    start_date=start_date,
                )


async def simulate_bookings(
    db: AsyncSession,
    *,
    users_count: int = 100,
    max_actions_per_user: int = 5,
) -> None:
    """
    Имитация бронирований сотней "пользователей".

    Каждый "пользователь" случайно выбирает действия:
    - забронировать одиночный слот (guest booking)
    - купить курс целиком (CourseBookingCreate)
    """
    random.seed(123)

    # Забираем все услуги и слоты
    services_result = await db.execute(select(Service))
    services = list(services_result.scalars().all())

    slots_result = await db.execute(
        select(Slot).where(Slot.start_time >= date.today())
    )
    slots = list(slots_result.scalars().all())

    course_services = [s for s in services if s.type == ServiceType.COURSE]

    single_slots = [s for s in slots if s.service_id is None or any(
        srv.id == s.service_id and srv.type == ServiceType.SINGLE_CLASS
        for srv in services
    )]

    course_slots = [s for s in slots if any(
        srv.id == s.service_id and srv.type == ServiceType.COURSE
        for srv in services
    )]

    print(
        f"[simulate] services={len(services)}, "
        f"course_services={len(course_services)}, "
        f"slots={len(slots)}, "
        f"single_slots={len(single_slots)}, "
        f"course_slots={len(course_slots)}"
    )

    course_success = 0
    course_failed = 0
    single_success = 0
    single_failed = 0

    for user_idx in range(users_count):
        actions = random.randint(1, max_actions_per_user)
        for _ in range(actions):
            action_type = random.choice(["single", "course"])

            guest_name = f"Guest {user_idx}"
            guest_email = f"guest{user_idx}@example.com"

            if action_type == "course" and course_services:
                service = random.choice(course_services)
                schema = CourseBookingCreate(
                    service_id=service.id,
                    guest_name=guest_name,
                    guest_email=guest_email,
                    guest_phone=None,
                )
                try:
                    await create_course_booking(db, schema=schema)
                    course_success += 1
                except HTTPException:
                    # Ожидаемо при отсутствии мест / конфликте
                    course_failed += 1
                continue

            # single booking
            if not single_slots:
                continue
            slot = random.choice(single_slots)
            schema = BookingCreate(
                slot_id=slot.id,
                guest_name=guest_name,
                guest_email=guest_email,
                guest_phone=None,
            )
            try:
                await create_booking(db, schema)
                single_success += 1
            except HTTPException:
                single_failed += 1

    print(
        f"[simulate] single_success={single_success}, "
        f"single_failed={single_failed}, "
        f"course_success={course_success}, "
        f"course_failed={course_failed}"
    )


async def main() -> None:
    """
    Точка входа:
    1) сидируем данные (если таблицы пустые)
    2) запускаем симуляцию бронирований
    """
    async with async_session_maker() as db:
        # Простая эвристика: если услуг нет — сидируем.
        result = await db.execute(select(Service))
        existing_services = list(result.scalars().all())
        if not existing_services:
            print("[seed] no services found, seeding demo data...")
            await seed_demo_data(db)
        else:
            print(f"[seed] found {len(existing_services)} services, skipping seeding.")

        print("[simulate] starting bookings simulation...")
        await simulate_bookings(db)
        print("[done] simulation finished.")


if __name__ == "__main__":
    asyncio.run(main())

