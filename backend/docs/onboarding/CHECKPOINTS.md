# Checkpoints — проверка понимания

> Отвечай **своими словами**, указывая файлы/символы.
> Ключи в `<details>` — для самопроверки после ответа, не для первого прохода.

---

## Шаг 0 — Inventory

1. Какие домены лежат в `app/modules/` и какой из них «лист» (leaf)?
2. Почему ORM-модели централизованы в `app/models/`, а не разложены по модулям? (источник: ADR)
3. Что такое published interface модуля и где он живёт?
4. Какая зависимость запрещена: `catalog → booking` или `booking → catalog`?
5. Чем `import-linter` отличается от `tests/architecture/`?

<details>
<summary>Ключи (заполняет A9 / Orchestrator)</summary>

1. Домены: `auth`, `identity`, `catalog`, `booking`, `payment`, `search`. Leaf: `identity` и `search` (не тянут другие домены; контракты import-linter + `docs/ARCHITECTURE.md`).
2. ADR-003 §2: плотный FK-граф + cross-domain loads; split моделей = риск циклов; YAGNI до service-split.
3. Публичный контракт домена — символы в `modules/<domain>/__init__.py` (`__all__`, иногда lazy `__getattr__`). Пример: `from app.modules.booking import is_own_booking`.
4. Запрещён **`catalog → booking`** (и catalog → payment/auth). `booking → catalog` разрешён через published catalog API.
5. `import-linter` (`backend/pyproject.toml`) — граф импортов пакетов; `tests/architecture/` — AST-гейты (repos не импортируют service/router/policies; нет `_` cross-domain). Оба в CI.

</details>

---

## Шаг 1 — Bootstrap

1. Что происходит при старте и при остановке приложения (`lifespan`)?
2. Какие security headers выставляются всегда, какие — только в production?
3. Где монтируются `/api/v1` роутеры и отдельно webhooks?
4. Зачем в `api/router.py` вызывается `model_rebuild()`?
5. Как request_id попадает в логи и в ответ?

<details>
<summary>Ключи</summary>

1. Startup: `setup_logging()`; shutdown: `await engine.dispose()` — `lifespan` в `app/main.py`.
2. Всегда: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` (`SecurityHeadersMiddleware`). HSTS — только если `settings.is_production`. CSP API-режима не на `/docs`/`/redoc`/`/openapi.json`.
3. `register_routers` (`api/router.py`): health (± `/api/v1`), `metrics`, domain routers в `api_v1` (`prefix=/api/v1`), `webhooks_router` отдельно (`/webhooks/...`).
4. Материализовать forward refs / unions после `from __future__ import annotations` (booking/order/search schemas) до использования в response models.
5. `RequestLoggingMiddleware`: header `X-Request-ID` или `uuid4` → `request.state.request_id` + `structlog.contextvars`; тот же header на response; handlers читают через `_request_id` в Problem JSON.

</details>

---

## Шаг 2 — Persistence

1. Что такое `UnitOfWork` в этом проекте: объект с логикой или «сумка репозиториев»?
2. Кто вызывает `commit()` — service или deps/scope?
3. Зачем `uow.py` и `uow_factory.py` разделены?
4. Возьми `BookingStatus` — перечисли статусы из кода (не по памяти).
5. Как Alembic узнаёт о моделях для autogenerate?

<details>
<summary>Ключи</summary>

1. «Сумка репозиториев» + `session`; logic glue запрещён (ADR-003 §3, docstring `UnitOfWork` в `core/uow.py`).
2. При `Depends(get_uow)` — `uow_scope(auto_commit=True)` коммитит на успешном выходе (если service сам не вызвал `commit`). Service обычно не коммитит.
3. import-linter / ARCHITECTURE: wiring всех repository-классов — исключение только в `uow_factory`; `uow.py` остаётся лёгким типом.
4. `pending`, `confirmed`, `cancelled`, `expired`, `completed`, `no_show` (+ `ACTIVE_STATUSES` = pending/confirmed) — `models/booking.py`.
5. `alembic/env.py` → `target_metadata = Base.metadata`; модели экспортируются в `app/models/__init__.py` «для autogenerate». **UNKNOWN:** явный import `app.models` в `env.py` отсутствует — сверяй workflow перед autogenerate.

</details>

---

## Шаг 3 — Contracts

1. Почему request и response schema разделены?
2. Какой envelope у списков (pagination)?
3. Что такое Problem JSON в этом проекте (поля)?
4. Где живёт общий base repository / pagination helper?
5. Можно ли отдавать ORM-модель напрямую из router? Почему?

<details>
<summary>Ключи</summary>

1. Разные правила валидации create/update vs allowlist полей наружу (security, perspectives Self/Owner). Пример: identity `UserCreate`/`UserResponse`; booking исключает Stripe IDs из client schemas.
2. `PaginatedResponse[T]` = `{items, total, page, size}` — `core/pagination.py` (`build_paginated_response` / `pagination_offset`).
3. `_error_body` в `main.py`: `type`, `title`, `status`, `detail`, optional `request_id`. Для AppError: `type=app-error:{ClassName}`.
4. Write helpers: `WriteRepositoryMixin` в `core/repository.py`. Pagination: `core/pagination.py`. (Legacy `app/api/mappers/` пуст.)
5. **Нет.** ORM — persistence; router мапит через `model_validate` / `mapping.py` / `mappers.py`. Пример: `create_booking_endpoint` → `map_booking_created_response`.

</details>

---

## Шаг 4 — Auth + Identity

1. Где хранится refresh token (cookie vs body) и почему это важно?
2. Чем `identity` отличается от `auth` по ответственности?
3. Как проверяется членство в студии (модель + policy/dependency)?
4. Что происходит с soft-deleted user при попытке логина?
5. Какие публичные функции auth экспортирует для других модулей?

<details>
<summary>Ключи</summary>

1. httpOnly cookie `refresh_token` (не JSON body) — docstring `auth/router.py`; XSS не читает refresh. Плюс readable `csrf_token` + header `X-CSRF-Token` на refresh.
2. `auth` — OTP, JWT-сессии, cookies, account HTTP. `identity` — User lifecycle/profile/soft-delete + ownership policy; **без** своего router. Auth оркестрирует identity через published API.
3. Модель `StudioMember` + роль `StudioMemberRole`; enforce: `require_studio_permission` / `has_studio_permission` в `catalog/studio/service.py` (матрица `STUDIO_PERMISSIONS_BY_ROLE`). Не в `identity`, не в `deps.py`.
4. Lookups `get_user_by_id`/`get_by_email` скрывают soft-deleted → Bearer/`/me` = 401. Email анонимизирован; новый OTP verify создаёт **нового** User (`get_or_create_user` + тест delete-account). Не ориентироваться на устаревшую фразу ARCHITECTURE про «cannot authenticate again».
5. `modules/auth/__init__.py` `__all__`: `OTPCodeRepository`, `RefreshTokenRepository`, `get_current_user_from_token` (lazy). HTTP resolve пользователя — обычно `core.deps`, не этот symbol.

</details>

---

## Шаг 5 — Catalog

1. Связь Studio → Service → Occurrence: какие FK?
2. Зачем `ScheduleTemplate` и кто генерирует occurrences?
3. Чем `catalog/public` отличается от owner routers?
4. Какие статусы/visibility есть у Service / Occurrence?
5. Почему catalog не должен знать про payment?

<details>
<summary>Ключи</summary>

1. `Service.studio_id` → studios; `Occurrence.studio_id` + `Occurrence.service_id` (+ optional `schedule_template_id`, `instructor_id`). Иерархия: Studio → Service → Occurrence.
2. Template — метаданные повторения (weekday + wall-clock). Bulk slots: `occurrence_generator` в `catalog/schedule/service.py` (параметрический; **не** читает template и не пишет `schedule_template_id`). Manual: `create_occurrence`.
3. `public`: анонимная витрина `GET /studios/slug/{slug}/public` → `get_studio_public` (только published/bookable). Owner/dashboard: auth + `require_studio_permission`, видит draft при `manage_services`.
4. Service: `ServiceVisibility` = `draft`/`published`/`archived` (+ legacy `is_active`). Occurrence: `OccurrenceStatus` = `scheduled`/`cancelled`/`completed`.
5. Allowed edges + import-linter: catalog ↛ payment (и booking/auth). Checkout/course order живут в payment/booking — catalog остаётся продуктовым слоем (ADR-003 / ARCHITECTURE).

</details>

---

## Шаг 6 — Booking

1. Что такое pending hold и где TTL/expire логика?
2. Как обеспечивается capacity / уникальность активного бронирования?
3. Роль `Order` относительно `Booking`.
4. Что делает lifecycle job каждые 5 минут?
5. Где лежат policies вроде `is_own_booking` и кто их вызывает?

<details>
<summary>Ключи</summary>

1. `BookingStatus.PENDING` + `reserved_until` = `now + BOOKING_HOLD_MINUTES` (`core/booking_holds.py`, default 15). Capacity: только active hold (`reserved_until > now`). Статус чистит `expire_stale_pending` (cron).
2. Три уровня: FOR UPDATE на occurrence; counts confirmed + active pending vs `max_capacity`; DB partial unique на `(occurrence, guest_email|user_id)` WHERE status IN pending/confirmed + soft `ensure_no_active_*` → race `ConflictError`.
3. Course: один `Order` (PENDING) → N `Booking` (COURSE, общий order `access_token`). Single: booking без order (legacy). Confirm/pay — через payment.
4. `run_booking_lifecycle`: `expire_stale_pending` затем `complete_past_confirmed` в одном `uow_scope` (`scripts/run_booking_lifecycle.py`; Render `*/5`).
5. `modules/booking/policies.py` (`is_own_booking`, `can_access_booking`); published на корне booking. Снаружи: **payment** `access.py` → `is_own_booking` (checkout gate).

</details>

---

## Шаг 7 — Payment

1. Последовательность: create checkout → webhook → confirm seats.
2. Зачем `ProcessedWebhookEvent`?
3. Что такое ledger / `manual_review` в этом коде?
4. Где граница `integrations/stripe` vs `modules/payment`?
5. Что блокирует оплату, если Connect не готов?

<details>
<summary>Ключи</summary>

1. `create_checkout_session` / `create_order_checkout_session` → Stripe Session → `POST /webhooks/stripe` → `process_stripe_webhook_event` → `record_checkout_completed_payment` → `confirm_*_after_payment` (если paid).
2. Идемпотентность по Stripe `event.id` (таблица `processed_webhook_events`); статус booking/order недостаточен для safe skip. Read: `exists_by_event_id`; race: unique + IntegrityError.
3. Ledger = локальные `Payment`/`Refund` rows (`ledger.py`). `manual_review` / `overbooked_manual_review` — деньги есть, seat не подтверждён безопасно (capacity/overbook); auto-refund нет.
4. `integrations/stripe` — pure builders params (`build_*_checkout_params`). `modules/payment` — access, Connect gate, hold, DB, webhooks, capacity, ledger. IO client: `payment/stripe_client.py`.
5. `_require_connect_account_for_checkout`: нужны `studio.stripe_account_id` **и** `studio.stripe_charges_enabled`, иначе `ValidationError` до `sessions.create`.

</details>

---

## Шаг 8 — Search + Ops

1. Search — отдельный write-домен или read-only leaf?
2. Какие cron/scripts есть и идемпотентны ли они?
3. Где rate limiting и что будет без Redis в multi-instance?
4. Какие метрики/health отдаёт API?
5. Как локально прогнать booking-lifecycle?

<details>
<summary>Ключи</summary>

1. Read-only leaf: `GET /api/v1/search` → `SearchRepository` читает studios/services; контракт `search is read-only leaf` (↛ booking/catalog/payment/auth).
2. Jobs: `run_booking_lifecycle` (идемпотентен), OTP cleanup Python/local + `pg_cron_otp_cleanup.sql` prod (идемпотентны), `seed_100_studios` — **не** job (destructive truncate). См. guide 08 таблицу.
3. SlowAPI `limiter` в `core/rate_limit.py` (+ `app.state.limiter`). Без `REDIS_URL` — in-memory per process → раздельные счётчики на репликах.
4. `GET /metrics` — Prometheus (`generate_latest`, в т.ч. `zeeframe_domain_events_total`). `GET /health` — DB + version, **503** если DB fail; `/health/ready` — DB + optional Stripe/Resend (503 только при DB fail).
5. `make booking-lifecycle` или `cd backend && uv run python -m scripts.run_booking_lifecycle`.

</details>

---

## Шаг 9 — Synthesis

1. Нарисуй sequence: guest создаёт booking и платит (модули + ключевые функции).
2. Что случится, если webhook пришёл дважды?
3. Что случится, если hold истёк, а оплата пришла позже?
4. Куда положить новый endpoint «список моих заказов» и какие слои создать?
5. Какой тест/линтер упадёт, если `catalog` импортирует `payment.service`?

<details>
<summary>Ключи</summary>

1. `booking.create_booking` (PENDING + hold + access_token) → `payment.create_checkout_session` → Stripe → `webhooks.stripe_webhook` → `process_stripe_webhook_event` → `confirm_booking_after_payment` → CONFIRMED. (Course: `create_course_booking` + `create_order_checkout_session` + `confirm_order_after_payment`.) Детали — `guides/09-synthesis.md` scenario 1.
2. Второй раз: `exists_by_event_id` → skip (`webhook_duplicate_event_skipped`); confirm/ledger side effects не повторяются. Race: unique `event_id` → IntegrityError / duplicate_race. Таблица `processed_webhook_events`.
3. Checkout create после expire — отказ (`Booking hold has expired`). Уже созданный Session + paid webhook: `EXPIRED` ∈ confirmable; при free capacity → revive CONFIRMED/PAID; при overbook → `manual_review` / `overbooked_manual_review`, seat cancelled.
4. Уже есть `GET /api/v1/orders/my` в `booking/order`. Если с нуля: router + schemas в `modules/booking/order/`, service `get_my_orders`, `OrderRepository`, mount в `api/router.py`, auth `get_current_user_required`. Не в catalog/payment.
5. import-linter contract `catalog does not depend on booking/payment/auth` (+ `uv run lint-imports` / CI). Architecture suite может дополнительно ловить границы.

**Доп. self-exam (guide 09):** commit в `uow_scope`; ownership vs studio RBAC; CONFIRMED только payment; Connect gate; `make booking-lifecycle` идемпотентен.

</details>
