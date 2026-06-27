"""
Seed bookable studio + occurrence for Playwright E2E (guest checkout flow).

Prints a single JSON line to stdout:
  {
    "studioId": 1,
    "occurrenceId": 2,
    "occurrenceDate": "2026-06-17",
    "ownerAccessToken": "..."
  }

Run from backend directory:
    uv run python -m scripts.e2e_seed
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import time, timedelta

from sqlalchemy import select

from app.core.datetime_utils import studio_local_date_now, studio_local_to_utc
from app.core.security import create_access_token
from app.core.uow_factory import uow_scope
from app.models.service import Service
from app.models.studio import Studio
from app.models.user import User
from app.modules.catalog.occurrence import OccurrenceCreate, create_occurrence
from app.modules.catalog.studio import StudioCreate, create_studio

E2E_OWNER_EMAIL = "e2e-seed-owner@example.com"
E2E_STUDIO_NAME = "E2E Yoga Studio"


async def seed_e2e_bookable_occurrence() -> dict[str, int | str]:
    """Create or reuse E2E owner, studio, and a paid occurrence with capacity."""
    async with uow_scope() as uow:
        user = await uow.users.get_by_email(E2E_OWNER_EMAIL)
        if user is None:
            user = User(
                email=E2E_OWNER_EMAIL,
                name="E2E Seed Owner",
                phone=None,
                is_active=True,
            )
            uow.session.add(user)
            await uow.session.flush()
            await uow.session.refresh(user)

        result = await uow.session.execute(
            select(Studio).where(Studio.slug == "e2e-yoga")
        )
        studio = result.scalar_one_or_none()
        if studio is None:
            studio_schema = StudioCreate(
                name=E2E_STUDIO_NAME,
                slug="e2e-yoga",
                description="Playwright guest checkout E2E",
                logo_url=None,
                cover_url=None,
                email="e2e-yoga@example.com",
                phone=None,
                address="1 E2E Street",
                city="Dublin",
                latitude=None,
                longitude=None,
                cancel_before_hours=24,
                owner_id=user.id,
                timezone="Europe/Dublin",
            )
            studio = await create_studio(uow, studio_schema)
            await uow.session.flush()

        tz_name = "Europe/Dublin"
        service_result = await uow.session.execute(
            select(Service).where(
                Service.studio_id == studio.id,
                Service.name == "E2E Morning Flow",
            )
        )
        service = service_result.scalar_one_or_none()
        if service is None:
            service = Service(
                studio_id=studio.id,
                name="E2E Morning Flow",
                description="Automated E2E test session",
                type="single",
                duration_minutes=60,
                max_capacity=10,
                price_single_cents=2500,
            )
            uow.session.add(service)
            await uow.session.flush()
            await uow.session.refresh(service)

        session_date = studio_local_date_now(tz_name) + timedelta(days=1)
        start = studio_local_to_utc(session_date, time(10, 0), tz_name)
        end = studio_local_to_utc(session_date, time(11, 0), tz_name)
        occurrence_schema = OccurrenceCreate(
            start_time=start,
            end_time=end,
            title="E2E Morning Flow",
            description="Automated E2E test session",
            max_capacity=10,
            price_cents=2500,
            course_price_cents=None,
            studio_id=studio.id,
            service_id=service.id,
            instructor_id=None,
        )
        occurrence = await create_occurrence(uow, occurrence_schema)

        owner_access_token = create_access_token(user.id, user.email)
        occurrence_date = session_date.isoformat()

        return {
            "studioId": studio.id,
            "occurrenceId": occurrence.id,
            "occurrenceDate": occurrence_date,
            "ownerAccessToken": owner_access_token,
        }


async def main() -> None:
    payload = await seed_e2e_bookable_occurrence()
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    asyncio.run(main())
