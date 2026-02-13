from __future__ import annotations

"""
Скрипт для инициализации БД реальными студиями в Ирландии для тестирования поиска.

Запуск (из директории backend):

    uv run python -m app.seed

Скрипт:
- очищает данные по студиям/услугам (TRUNCATE с RESTART IDENTITY)
- гарантирует наличие пользователя с id=1 (owner)
- создаёт 60 студий в городах Ирландии
- для каждой студии создаёт 3–8 услуг разных категорий и типов
"""

import asyncio
import json
import random
from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models import Service, ServiceCategory, ServiceType, Studio, User


@dataclass
class CityConfig:
    name: str
    count: int
    lat: float
    lng: float
    lat_jitter: float
    lng_jitter: float


CITY_CONFIGS: Sequence[CityConfig] = [
    CityConfig("Dublin", count=30, lat=53.3498, lng=-6.2603, lat_jitter=0.05, lng_jitter=0.08),
    CityConfig("Cork", count=15, lat=51.8985, lng=-8.4756, lat_jitter=0.03, lng_jitter=0.05),
    CityConfig("Galway", count=10, lat=53.2707, lng=-9.0568, lat_jitter=0.03, lng_jitter=0.05),
    CityConfig("Limerick", count=5, lat=52.6638, lng=-8.6267, lat_jitter=0.03, lng_jitter=0.05),
]

AMENITIES_POOL: list[str] = [
    "shower",
    "parking",
    "towels",
    "smoothie_bar",
    "lockers",
    "wifi",
]

VIBE_TAGS: list[str] = [
    "#Techno",
    "#BeginnerFriendly",
    "#HighIntensity",
    "#MorningVibe",
    "#SlowFlow",
    "#Community",
    "#DeepWork",
]

STUDIO_NAME_PREFIXES: list[str] = [
    "Neon",
    "Pulse",
    "Ethereal",
    "Iron",
    "Velvet",
    "Midnight",
    "Urban",
    "Gravity",
    "Aurora",
    "Echo",
    "Flux",
    "Nova",
]

STUDIO_NAME_SUFFIXES: list[str] = [
    "Studio",
    "Loft",
    "House",
    "Collective",
    "Club",
    "Space",
    "Lab",
    "Movement",
    "Flow",
    "Forge",
]

STREET_NAMES: list[str] = [
    "Temple Lane",
    "Riverwalk",
    "Harbour Street",
    "Greenway Road",
    "Market Street",
    "Liberty Lane",
    "Canal Quay",
    "Phoenix Road",
]


def random_coords(config: CityConfig) -> tuple[float, float]:
    lat = config.lat + random.uniform(-config.lat_jitter, config.lat_jitter)
    lng = config.lng + random.uniform(-config.lng_jitter, config.lng_jitter)
    return round(lat, 6), round(lng, 6)


def random_studio_name() -> str:
    prefix = random.choice(STUDIO_NAME_PREFIXES)
    suffix = random.choice(STUDIO_NAME_SUFFIXES)
    return f"{prefix} {suffix}"


def random_address(city: str) -> str:
    street = random.choice(STREET_NAMES)
    number = random.randint(3, 128)
    return f"{number} {street}, {city}, Ireland"


def random_amenities() -> list[str]:
    k = random.randint(2, 4)
    return sorted(random.sample(AMENITIES_POOL, k=k))


def random_service_name(category: ServiceCategory) -> str:
    base_by_category: dict[ServiceCategory, Sequence[str]] = {
        ServiceCategory.YOGA: ["Slow Flow", "Power Vinyasa", "Neon Zen", "Ethereal Yoga"],
        ServiceCategory.BOXING: ["Power Boxing", "Night Fight Club", "Box & Burn"],
        ServiceCategory.DANCE: ["Contemporary Waves", "House Grooves", "Studio Dance"],
        ServiceCategory.HIIT: ["HIIT Blast", "Midnight HIIT", "Turbo Burn"],
        ServiceCategory.PILATES: ["Reformer Core", "Iron & Flow", "Boutique Pilates"],
        ServiceCategory.MARTIAL_ARTS: ["Dojo Flow", "Modern Combat", "Martial Arts Lab"],
        ServiceCategory.STRENGTH: ["Strength Forge", "Iron Room", "Barbell Club"],
    }
    options = base_by_category.get(category, ["Signature Class"])
    return random.choice(list(options))


def random_vibe_tags() -> list[str]:
    k = random.randint(2, 3)
    return random.sample(VIBE_TAGS, k=k)


async def ensure_owner(db: AsyncSession) -> User:
    """Убедиться, что пользователь с id=1 существует (используется как владелец студий)."""
    owner = await db.get(User, 1)
    if owner is not None:
        return owner

    owner = User(
        id=1,
        email="owner1@example.com",
        name="Studio Owner 1",
        phone=None,
        is_active=True,
    )
    db.add(owner)
    await db.flush()
    await db.refresh(owner)
    return owner


async def truncate_studios_and_services(db: AsyncSession) -> None:
    """Очистить таблицы студий и услуг (и зависимые данные) перед сидированием."""
    # Проверяем, есть ли уже студии
    existing_count = await db.scalar(select(func.count(Studio.id)))
    if existing_count and existing_count > 0:
        print(f"[seed] found {existing_count} studios, truncating studios and services...")
        # TRUNCATE с CASCADE, чтобы очистить зависимые записи (slots, bookings и т.п.)
        await db.execute(
            text("TRUNCATE TABLE services, studios RESTART IDENTITY CASCADE")
        )
        await db.flush()
    else:
        print("[seed] no studios found, seeding fresh data...")


async def seed_ireland_studios(db: AsyncSession) -> None:
    """Создать 60 студий в Ирландии с услугами для теста поиска."""
    random.seed(2026)

    await truncate_studios_and_services(db)
    owner = await ensure_owner(db)

    studios: list[Studio] = []

    # === Создаём студии по городам ===
    for cfg in CITY_CONFIGS:
        for _ in range(cfg.count):
            lat, lng = random_coords(cfg)
            studio = Studio(
                owner_id=owner.id,
                name=random_studio_name(),
                description="Boutique studio focused on curated movement experiences.",
                email=None,
                phone=None,
                address=random_address(cfg.name),
                city=cfg.name,
                latitude=lat,
                longitude=lng,
                amenities=random_amenities(),
                is_active=True,
            )
            studios.append(studio)
            db.add(studio)

    await db.flush()  # чтобы у студий появились id

    # === Создаём услуги для каждой студии ===
    all_categories: list[ServiceCategory] = list(ServiceCategory)

    services_created = 0
    for studio in studios:
        services_count = random.randint(3, 8)
        for _ in range(services_count):
            category = random.choice(all_categories)
            is_course = random.choice([True, False])
            service_type = (
                ServiceType.COURSE if is_course else ServiceType.SINGLE_CLASS
            )

            duration_minutes = random.choice([45, 60, 75, 90])
            max_capacity = random.choice([8, 10, 12, 14, 16, 18])

            price_single = random.randrange(1500, 2600, 100)  # 15–25 € за класс
            price_course = (
                random.randrange(8000, 16000, 500) if is_course else None
            )  # 80–160 € за курс

            tags = random_vibe_tags()

            await db.execute(
                text(
                    """
                    INSERT INTO services (
                        studio_id,
                        name,
                        description,
                        type,
                        category,
                        duration_minutes,
                        max_capacity,
                        price_single_cents,
                        price_course_cents,
                        soft_limit_ratio,
                        hard_limit_ratio,
                        max_overbooked_ratio,
                        tags,
                        is_active
                    )
                    VALUES (
                        :studio_id,
                        :name,
                        :description,
                        :type,
                        :category,
                        :duration_minutes,
                        :max_capacity,
                        :price_single_cents,
                        :price_course_cents,
                        :soft_limit_ratio,
                        :hard_limit_ratio,
                        :max_overbooked_ratio,
                        :tags,
                        TRUE
                    )
                    """
                ),
                {
                    "studio_id": studio.id,
                    "name": random_service_name(category),
                    "description": f"{category.value.title()} experience tailored to urban movers.",
                    "type": service_type,
                    "category": category.value,
                    "duration_minutes": duration_minutes,
                    "max_capacity": max_capacity,
                    "price_single_cents": price_single,
                    "price_course_cents": price_course,
                    "soft_limit_ratio": 1.1 if is_course else 1.0,
                    "hard_limit_ratio": 1.5,
                    "max_overbooked_ratio": 0.3 if is_course else 0.0,
                    "tags": json.dumps(tags),
                },
            )

            services_created += 1

    await db.commit()

    studio_count = await db.scalar(select(func.count(Studio.id)))
    service_count = await db.scalar(select(func.count(Service.id)))
    print(f"[seed] created studios: {studio_count}, services: {service_count}")


async def main() -> None:
    async with async_session_maker() as db:
        await seed_ireland_studios(db)


if __name__ == "__main__":
    asyncio.run(main())

