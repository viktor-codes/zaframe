"""
Seed 100 studios with 100 distinct owners for frontend visual testing.

Run (from backend directory):
    uv run python -m app.scripts.seed_100_studios

This script:
- truncates studios/services (CASCADE clears dependent rows like slots/bookings/orders)
- deletes previously seeded owners by email prefix to avoid user table bloat
- creates 100 owners + 100 studios across Irish cities
- creates 3–8 services per studio (so frontend can render include_services)
"""

from __future__ import annotations

import asyncio
import json
import random
import re
from dataclasses import dataclass

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models import Service, ServiceCategory, ServiceType, Studio, User


@dataclass(frozen=True)
class CityConfig:
    name: str
    count: int
    lat: float
    lng: float
    lat_jitter: float
    lng_jitter: float


CITY_CONFIGS: list[CityConfig] = [
    CityConfig("Dublin", count=50, lat=53.3498, lng=-6.2603, lat_jitter=0.05, lng_jitter=0.08),
    CityConfig("Cork", count=25, lat=51.8985, lng=-8.4756, lat_jitter=0.03, lng_jitter=0.05),
    CityConfig("Galway", count=15, lat=53.2707, lng=-9.0568, lat_jitter=0.03, lng_jitter=0.05),
    CityConfig("Limerick", count=10, lat=52.6638, lng=-8.6267, lat_jitter=0.03, lng_jitter=0.05),
]

AMENITIES_POOL: list[str] = [
    "shower",
    "parking",
    "towels",
    "smoothie_bar",
    "lockers",
    "wifi",
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

VIBE_TAGS: list[str] = [
    "#Techno",
    "#BeginnerFriendly",
    "#HighIntensity",
    "#MorningVibe",
    "#SlowFlow",
    "#Community",
    "#DeepWork",
]


def _slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "studio"


def _random_coords(cfg: CityConfig) -> tuple[float, float]:
    lat = cfg.lat + random.uniform(-cfg.lat_jitter, cfg.lat_jitter)
    lng = cfg.lng + random.uniform(-cfg.lng_jitter, cfg.lng_jitter)
    return round(lat, 6), round(lng, 6)


def _random_studio_name() -> str:
    return f"{random.choice(STUDIO_NAME_PREFIXES)} {random.choice(STUDIO_NAME_SUFFIXES)}"


def _random_address(city: str) -> str:
    return f"{random.randint(3, 128)} {random.choice(STREET_NAMES)}, {city}, Ireland"


def _random_amenities() -> list[str]:
    return sorted(random.sample(AMENITIES_POOL, k=random.randint(2, 4)))


def _random_vibe_tags() -> list[str]:
    return random.sample(VIBE_TAGS, k=random.randint(2, 3))


def _random_service_name(category: ServiceCategory) -> str:
    base_by_category: dict[ServiceCategory, list[str]] = {
        ServiceCategory.YOGA: ["Slow Flow", "Power Vinyasa", "Neon Zen", "Ethereal Yoga"],
        ServiceCategory.BOXING: ["Power Boxing", "Night Fight Club", "Box & Burn"],
        ServiceCategory.DANCE: ["Contemporary Waves", "House Grooves", "Studio Dance"],
        ServiceCategory.HIIT: ["HIIT Blast", "Midnight HIIT", "Turbo Burn"],
        ServiceCategory.PILATES: ["Reformer Core", "Iron & Flow", "Boutique Pilates"],
        ServiceCategory.MARTIAL_ARTS: ["Dojo Flow", "Modern Combat", "Martial Arts Lab"],
        ServiceCategory.STRENGTH: ["Strength Forge", "Iron Room", "Barbell Club"],
    }
    return random.choice(base_by_category.get(category, ["Signature Class"]))


async def _truncate_studios_and_services(db: AsyncSession) -> None:
    await db.execute(text("TRUNCATE TABLE services, studios RESTART IDENTITY CASCADE"))
    await db.flush()


async def _delete_seed_owners(db: AsyncSession) -> None:
    # Avoid deleting real users; only delete our known seed patterns.
    await db.execute(
        text(
            """
            DELETE FROM users
            WHERE email LIKE 'seed-owner-%@example.com'
               OR email LIKE 'seed-demo-owner-%@example.com'
            """
        )
    )
    await db.flush()


async def seed_100_studios(db: AsyncSession) -> None:
    random.seed(2026)

    await _truncate_studios_and_services(db)
    await _delete_seed_owners(db)

    studios: list[Studio] = []

    studio_idx = 0
    for cfg in CITY_CONFIGS:
        for _ in range(cfg.count):
            studio_idx += 1

            owner = User(
                email=f"seed-owner-{studio_idx:03d}@example.com",
                name=f"Seed Owner {studio_idx:03d}",
                phone=None,
                is_active=True,
            )
            db.add(owner)
            await db.flush()
            await db.refresh(owner)

            lat, lng = _random_coords(cfg)
            name = _random_studio_name()
            base_slug = _slugify(f"{name}-{cfg.name}-{studio_idx}")

            studio = Studio(
                owner_id=owner.id,
                name=name,
                slug=base_slug,
                description="Boutique studio focused on curated movement experiences.",
                email=None,
                phone=None,
                address=_random_address(cfg.name),
                city=cfg.name,
                latitude=lat,
                longitude=lng,
                amenities=_random_amenities(),
                is_active=True,
            )
            db.add(studio)
            studios.append(studio)

    await db.flush()  # ensure studio ids are assigned

    # Create services for each studio via SQL to keep it fast.
    all_categories: list[ServiceCategory] = list(ServiceCategory)
    for studio in studios:
        for _ in range(random.randint(3, 8)):
            category = random.choice(all_categories)
            is_course = random.choice([True, False])
            service_type = ServiceType.COURSE if is_course else ServiceType.SINGLE_CLASS

            duration_minutes = random.choice([45, 60, 75, 90])
            max_capacity = random.choice([8, 10, 12, 14, 16, 18])

            price_single = random.randrange(1500, 2600, 100)
            price_course = random.randrange(8000, 16000, 500) if is_course else None

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
                    "name": _random_service_name(category),
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
                    "tags": json.dumps(_random_vibe_tags()),
                },
            )

    await db.commit()

    studio_count = await db.scalar(select(func.count(Studio.id)))
    service_count = await db.scalar(select(func.count(Service.id)))
    owner_count = await db.scalar(
        select(func.count(User.id)).where(User.email.like("seed-owner-%@example.com"))
    )
    print(
        f"[seed_100] owners={owner_count}, studios={studio_count}, services={service_count}"
    )


async def main() -> None:
    async with async_session_maker() as db:
        await seed_100_studios(db)


if __name__ == "__main__":
    asyncio.run(main())

