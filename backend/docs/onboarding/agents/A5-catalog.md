# Agent A5 — Catalog (studio, service, schedule, occurrence, public)

## Роль

Ты — senior backend tech lead. Объясняешь продуктовую иерархию каталога: что студия продаёт и как появляются слоты (occurrences), **до** бронирования.

## Выход

`backend/docs/onboarding/guides/05-catalog.md`

## Whitelist

- `backend/app/modules/catalog/**`
- Models:
  - `backend/app/models/studio.py`
  - `backend/app/models/service.py`
  - `backend/app/models/schedule_template.py`
  - `backend/app/models/occurrence.py`
  - `backend/app/models/studio_member.py`
- Migrations (product/lifecycle/media/rbac related):
  - `009_studio_media_urls.py`, `010_rbac_studio_members.py`, `011_instructors_attendance.py`, `014_catalog_product_lifecycle.py`
  - и другие, если реально трогают catalog-таблицы (проверить, не гадать)
- `backend/app/core/datetime_utils.py` + `backend/docs/adr/001-datetime-and-studio-timezone.md`
- Tests:
  - `backend/tests/unit/catalog/**`
  - `backend/tests/integration/api/test_catalog_product_lifecycle.py`
  - `backend/tests/integration/api/test_studio_rbac.py`
- `docs/ARCHITECTURE.md`, ADR-003 (catalog edges)
- Guides 00–02 for links

**Запрещено:** booking create/payment; импортировать/описывать payment modules; менять код.

## Задачи исследования

1. Subdomains: `studio`, `service`, `schedule`, `occurrence`, `public` — ответственность каждого.
2. Published interfaces каждого `__init__.py` subdomain.
3. Иерархия и lifecycle: создание studio → service → schedule template → occurrences.
4. Availability helpers (`availability.py`, `availability_stats.py`) — зачем, кто вызывает.
5. Public vs authenticated/owner endpoints — разные routers/schemas.
6. Product lifecycle / visibility / statuses — из моделей + migration 014 + тесты.
7. RBAC на студийные write-операции — какие permissions проверяются (символы).
8. Explore/search-within-catalog (`studio/explore.py`) vs module `search` — граница.

## Обязательный контент

1. Mermaid class/ER: Studio–Service–ScheduleTemplate–Occurrence–StudioMember.
2. Sequence: owner создаёт service и генерирует/создаёт occurrences (по реальному коду).
3. Walkthrough ключевых public service functions в каждом subdomain (не обязательно каждая private `_` — но все export/public из service.py модулей).
4. Таблица routers: prefix + ключевые routes → service functions.
5. Why catalog cannot import booking/payment — со ссылкой на ARCHITECTURE/ADR.
6. 5+ checkpoint questions.
7. What to watch out for: timezone студии, capacity fields на occurrence, soft lifecycle статусы.

## DoD

- [ ] Все 5 subdomain папок отражены
- [ ] Нет booking/payment флоу
- [ ] Enum/status значения из кода
- [ ] Код не изменён

## Язык

Русский + точные символы.
