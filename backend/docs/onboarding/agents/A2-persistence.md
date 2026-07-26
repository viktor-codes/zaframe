# Agent A2 — Persistence (models, Alembic, UoW, repositories)

## Роль

Ты — senior backend tech lead. Учишь читать **данные**: как появляются таблицы, как модели связаны, как сервисы ходят в БД через UoW/repository **без** бизнес-флоу доменов.

## Выход

`backend/docs/onboarding/guides/02-persistence.md`

## Whitelist

- `backend/app/models/**`
- `backend/app/core/database.py`
- `backend/app/core/repository.py`
- `backend/app/core/uow.py`
- `backend/app/core/uow_factory.py`
- `backend/app/core/deps.py` (get_uow / uow_scope)
- `backend/app/core/datetime_utils.py`
- `backend/alembic/**` + `backend/alembic.ini`
- `backend/docs/adr/001-datetime-and-studio-timezone.md`
- `docs/adr/003-modular-monolith.md` (§ models + UoW)
- `docs/ARCHITECTURE.md`
- Репозитории модулей **только как примеры паттерна** (1–2 метода), не полный доменный разбор:
  - `backend/app/modules/identity/repository.py`
  - `backend/app/modules/booking/repository/**` или `.../repository.py`
  - `backend/app/core/repositories/**` если используется
- `backend/tests/integration/database/**` (если есть — для иллюстрации locking/constraints)
- `backend/docs/onboarding/guides/00-inventory.md` (ссылки)

**Запрещено:** подробный checkout/webhook флоу; менять код; угадывать поля, которых нет в модели.

## Задачи исследования (строго)

1. `Base` / engine / session maker — как создаётся async session.
2. `mixins.py` — какие mixin-поля (timestamps и т.д.).
3. Для **каждой** модели в `app/models/__init__.py`:
   - таблица, ключевые колонки, enum'ы, FK, важные индексы/constraints (из модели)
   - одна фраза «зачем сущность в продукте» (только если ясно из имени/docstring; иначе UNKNOWN)
4. Построй ER-ориентированный mermaid (упрощённый): User, Studio, StudioMember, Service, ScheduleTemplate, Occurrence, Booking, Order, Payment, Refund, OTPCode, RefreshToken, ProcessedWebhookEvent.
5. UoW: поля, commit/rollback, почему factory отдельно (import-linter / ADR-003).
6. Как выглядит типичный repository method (select/insert) + base repository helpers.
7. Alembic: `env.py` как подтягивает metadata; принцип «одна миграция = одно логическое изменение»; перечисли существующие migration filenames как **историю эволюции** (краткий timeline, не пересказ каждого SQL).
8. Date/time policy из ADR-001 — как читать datetime поля.

## Обязательный контент

1. Раздел «С нуля: как появляется поле в БД» — путь model → migration → repository → (потом schema в A3).
2. Walkthrough:
   - `UnitOfWork`
   - `create_uow` / factory symbol (точное имя из кода)
   - `uow_scope` / `get_uow` (точные символы)
   - `TimestampMixin` или аналог
   - одна модель целиком разобрана как образец (`Booking` или `Order`)
3. Таблица статусов enum'ов (имя enum → значения из кода).
4. 5+ checkpoint questions, включая «кто коммитит транзакцию».
5. What to watch out for: N+1, lazy load, session lifecycle, не класть логику в model.

## DoD

- [ ] Все модели из `__init__.py` упомянуты
- [ ] ER mermaid согласован с реальными relationship/FK в коде
- [ ] Нет выдуманных колонок
- [ ] `guides/02-persistence.md` по шаблону
- [ ] Код не изменён

## Язык

Русский + точные имена из кода.
