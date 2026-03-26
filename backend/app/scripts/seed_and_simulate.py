"""
Утилита для сидирования демо-данных и имитации нагрузки.

Цели:
- создать N студий, у каждой по несколько услуг (single + course)
- сгенерировать расписание курсов и слоты для одиночных занятий
- симулировать пользователей: бронирования (single + course)
- прогнать публичные сценарии и листинги (поиск студий, доступность)
- опционально: создание Checkout Session (если настроен Stripe)

Все вызовы идут через UnitOfWork и доменные исключения (AppError).

Запуск (из директории backend):
    uv run python -m app.scripts.seed_and_simulate
"""

from __future__ import annotations

import argparse
import asyncio
import random
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select, text

from app.core.config import settings
from app.core.database import async_session_maker
from app.core.exceptions import AppError
from app.core.uow import UnitOfWork, create_uow
from app.models.service import Service, ServiceType
from app.models.slot import Slot
from app.models.studio import Studio
from app.models.user import User
from app.schemas.booking import BookingCreate
from app.schemas.service import (
    CourseBookingCreate,
    ServiceCreate,
    StudioPublicResponse,
)
from app.schemas.slot import SlotCreate
from app.schemas.studio import StudioCreate
from app.services.booking import create_booking
from app.services.payment import (
    create_checkout_session,
    create_order_checkout_session,
)
from app.services.service import (
    create_course_booking,
    create_service,
    get_service_availability,
    get_studio_public,
    occurrence_generator,
)
from app.services.slot import create_slot
from app.services.studio import create_studio, get_studios, get_studios_count


async def _get_or_create_owner(uow: UnitOfWork, idx: int) -> User:
    """
    Найти или создать владельца для демо.
    При повторном --force-seed пользователи остаются в БД — переиспользуем по email.
    """
    email = f"seed-demo-owner-{idx}@example.com"
    user = await uow.users.get_by_email(email)
    if user is not None:
        return user
    user = User(
        email=email,
        name=f"Demo Owner {idx}",
        phone=None,
        is_active=True,
    )
    uow.session.add(user)
    await uow.session.flush()
    await uow.session.refresh(user)
    return user


def _random_future_datetime(days_ahead: int, duration_minutes: int) -> tuple[datetime, datetime]:
    """Случайные start/end в будущем (UTC)."""
    d = date.today() + timedelta(days=random.randint(1, days_ahead))
    hour = random.choice([9, 10, 12, 14, 18, 19, 20])
    start = datetime.combine(d, time(hour, 0), tzinfo=UTC)
    end = start + timedelta(minutes=duration_minutes)
    return start, end


async def seed_demo_data(
    uow: UnitOfWork,
    *,
    studios_count: int = 8,
    min_services: int = 3,
    max_services: int = 5,
    weeks_count: int = 4,
    single_slots_per_service: int = 3,
) -> None:
    """
    Сидирует базу тестовыми студиями, услугами, расписанием курсов и слотами для single-class.
    """
    random.seed(42)

    start_date = date.today() + timedelta(days=7)

    for i in range(studios_count):
        owner = await _get_or_create_owner(uow, i)
        studio_schema = StudioCreate(
            name=f"Demo Studio {i + 1}",
            description="Demo studio for load testing",
            email=f"studio{i + 1}@example.com",
            phone=None,
            address="Demo Address",
            owner_id=owner.id,
        )
        studio = await create_studio(uow, studio_schema)
        studio.slug = f"demo-studio-{i + 1}"
        studio.city = "Dublin"
        await uow.session.flush()

        services_in_studio = random.randint(min_services, max_services)
        for j in range(services_in_studio):
            is_course = random.choice([True, False])
            service_type = ServiceType.COURSE if is_course else ServiceType.SINGLE_CLASS
            duration = random.choice([45, 60, 90])
            max_capacity = random.choice([8, 10, 12, 15])
            price_single = random.choice([1200, 1500, 1800])
            price_course = price_single * weeks_count if is_course else None

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
            data = service_schema.model_dump(exclude={"studio_id"})
            if hasattr(data.get("category"), "value"):
                data["category"] = data["category"].value
            service = await create_service(uow, studio_id=studio.id, data=data)

            if service.type == ServiceType.COURSE:
                await occurrence_generator(
                    uow,
                    studio_id=studio.id,
                    service_id=service.id,
                    days=[1, 3],
                    start_time=time(18, 0),
                    weeks_count=weeks_count,
                    start_date=start_date,
                )
            else:
                for _ in range(single_slots_per_service):
                    start_dt, end_dt = _random_future_datetime(21, duration)
                    slot_schema = SlotCreate(
                        studio_id=studio.id,
                        service_id=service.id,
                        start_time=start_dt,
                        end_time=end_dt,
                        title=f"{service.name} — Drop-in",
                        description=None,
                        max_capacity=max_capacity,
                        price_cents=price_single,
                    )
                    await create_slot(uow, slot_schema)

    print(f"[seed] created {studios_count} studios with services and slots.")


async def simulate_bookings(
    uow: UnitOfWork,
    *,
    users_count: int = 150,
    max_actions_per_user: int = 5,
) -> None:
    """
    Имитация бронирований: одиночные слоты и курсы.
    """
    random.seed(123)

    services_result = await uow.session.execute(select(Service))
    services = list(services_result.scalars().all())

    slots_result = await uow.session.execute(
        select(Slot).where(Slot.start_time >= datetime.now(UTC))
    )
    slots = list(slots_result.scalars().all())

    course_services = [s for s in services if s.type == ServiceType.COURSE]
    single_slots = [
        s
        for s in slots
        if s.service_id is not None
        and any(srv.id == s.service_id and srv.type == ServiceType.SINGLE_CLASS for srv in services)
    ]

    course_slots = [
        s
        for s in slots
        if any(srv.id == s.service_id and srv.type == ServiceType.COURSE for srv in services)
    ]

    print(
        f"[simulate] services={len(services)}, course_services={len(course_services)}, "
        f"slots={len(slots)}, single_slots={len(single_slots)}, course_slots={len(course_slots)}"
    )

    course_success = 0
    course_failed = 0
    single_success = 0
    single_failed = 0
    single_booking_ids: list[int] = []
    course_order_ids: list[int] = []

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
                    course_resp = await create_course_booking(uow, schema=schema)
                    course_success += 1
                    course_order_ids.append(course_resp.order.id)
                except AppError:
                    course_failed += 1
                continue

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
                booking = await create_booking(uow, schema)
                single_success += 1
                single_booking_ids.append(booking.id)
            except AppError:
                single_failed += 1

    print(
        f"[simulate] single: success={single_success}, failed={single_failed}; "
        f"course: success={course_success}, failed={course_failed}"
    )

    if not settings.STRIPE_SECRET_KEY:
        print("[payments] STRIPE_SECRET_KEY not set, skipping checkout-session simulation.")
        return

    max_single_sessions = min(25, len(single_booking_ids))
    max_course_sessions = min(15, len(course_order_ids))

    for booking_id in single_booking_ids[:max_single_sessions]:
        try:
            await create_checkout_session(
                uow,
                booking_id=booking_id,
                success_url="https://example.com/payments/success",
                cancel_url="https://example.com/payments/cancel",
            )
        except AppError as e:
            print(f"[payments] booking_id={booking_id} checkout error: {e.detail}")

    for order_id in course_order_ids[:max_course_sessions]:
        try:
            await create_order_checkout_session(
                uow,
                order_id=order_id,
                success_url="https://example.com/payments/success",
                cancel_url="https://example.com/payments/cancel",
            )
        except AppError as e:
            print(f"[payments] order_id={order_id} checkout error: {e.detail}")


async def simulate_public_flows(uow: UnitOfWork) -> None:
    """Публичные сценарии: студия по slug, доступность курса."""
    studios_result = await uow.session.execute(
        select(Studio)
        .where(
            Studio.slug.is_not(None),
            Studio.is_active.is_(True),
        )
        .limit(10)
    )
    studios = list(studios_result.scalars().all())
    if not studios:
        print("[public] no studios with slug, skipping.")
        return

    total_services = 0
    total_availability_calls = 0

    for studio in studios:
        try:
            public: StudioPublicResponse = await get_studio_public(uow, slug=studio.slug or "")
        except AppError as e:
            print(f"[public] get_studio_public slug={studio.slug} error: {e.detail}")
            continue

        total_services += len(public.services)
        course_ids = [
            svc.id
            for svc in public.services
            if svc.type == ServiceType.COURSE and svc.occurrences_count > 0
        ]
        for service_id in course_ids[:3]:
            try:
                await get_service_availability(uow, service_id=service_id)
                total_availability_calls += 1
            except AppError:
                pass

    print(
        f"[public] studios_checked={len(studios)}, services={total_services}, availability_calls={total_availability_calls}"
    )


async def simulate_list_and_search(uow: UnitOfWork, *, rounds: int = 30) -> None:
    """Нагрузка листингов и поиска: get_studios, get_studios_count."""
    random.seed(456)
    for _ in range(rounds):
        skip = random.randint(0, 50)
        limit = random.choice([10, 20, 50])
        await get_studios(uow, skip=skip, limit=limit, is_active=True)
        await get_studios_count(uow, is_active=True)
        await get_studios(uow, skip=0, limit=10, city="Dublin")
    print(f"[load] list/search rounds={rounds} done.")


async def truncate_studios_services(uow: UnitOfWork) -> None:
    """Очистить студии и услуги (CASCADE удалит слоты, бронирования, заказы)."""
    await uow.session.execute(text("TRUNCATE TABLE services, studios RESTART IDENTITY CASCADE"))
    await uow.session.flush()
    print("[seed] truncated studios and services.")


async def main(force_seed: bool = False) -> None:
    """
    1) Сидируем данные (при --force-seed сначала truncate)
    2) Симуляция бронирований (single + course)
    3) Публичные флоу (студия по slug, доступность)
    4) Нагрузка листингов и поиска
    """
    async with async_session_maker() as session:
        uow = create_uow(session)
        try:
            result = await uow.session.execute(select(Service))
            existing = list(result.scalars().all())
            if force_seed and existing:
                await truncate_studios_services(uow)
                existing = []
            if not existing:
                print("[seed] seeding demo data...")
                await seed_demo_data(uow)
            else:
                print(f"[seed] found {len(existing)} services, skipping seed.")

            print("[simulate] bookings...")
            await simulate_bookings(uow)
            print("[simulate] public flows...")
            await simulate_public_flows(uow)
            print("[simulate] list/search load...")
            await simulate_list_and_search(uow)

            await uow.commit()
            print("[done] commit ok.")
        except Exception:
            await uow.rollback()
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo data and run load simulation")
    parser.add_argument(
        "--force-seed",
        action="store_true",
        help="Truncate studios/services and re-seed before simulating",
    )
    args = parser.parse_args()
    asyncio.run(main(force_seed=args.force_seed))
