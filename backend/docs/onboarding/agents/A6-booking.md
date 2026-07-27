# Agent A6 — Booking + Order + Lifecycle

## Роль

Ты — senior backend tech lead. Это **ядро продукта**. Разжуй создание брони, order, capacity, policies, lifecycle expire/complete так, чтобы ученик понял каждую публичную функцию и зачем она.

## Выход

`backend/docs/onboarding/guides/06-booking.md`

## Whitelist

- `backend/app/modules/booking/**` (включая `order/`, `repository/`)
- Models: `booking.py`, `order.py` (+ связанные FK на occurrence/user)
- `backend/app/core/booking_holds.py`
- `backend/app/core/access_tokens.py` (если order access token)
- Scripts: `backend/scripts/run_booking_lifecycle.py` (и аналоги, если есть)
- Migrations: `002_booking_active_uniqueness.py`, `003_booking_expired_completed_indexes.py`, `006_booking_access_token.py`, `008_order_guest_phone.py`, `015_order_checkout_session_id.py` (+ другие booking/order если релевантны)
- Tests:
  - `backend/tests/unit/booking/**`
  - `backend/tests/integration/api/test_bookings_authz.py`
  - `backend/tests/integration/api/test_attach_guest_bookings.py`
  - `backend/tests/integration/database/test_occurrence_lock_deadlock.py` (если про locks capacity)
- `docs/ARCHITECTURE.md` (Background jobs / booking lifecycle)
- Catalog **только** через published API booking→catalog (не разбирать catalog заново)
- Payment **не разбирать** — только точки, где booking/order отдаёт данные наружу («дальше A7»)

**Запрещено:** полный Stripe webhook разбор; менять код; выдумывать статусы.

## Задачи исследования

1. Published interface `modules/booking/__init__.py` (+ order package).
2. Статусы `BookingStatus`, `BookingType`, `OrderStatus` — переходы, кто меняет.
3. Create booking flow (guest/auth): router → schemas → service → persistence/queries/repository.
4. Capacity / uniqueness / locks: где enforced (DB constraint vs code), связанные тесты.
5. Order: single vs course booking (`order/` package) — функции create/list.
6. Policies (`policies.py`): `is_own_booking` и др. — кто импортирует снаружи.
7. `lifecycle.py`: expire pending, complete past confirmed — идемпотентность, связь с order/access token.
8. Mapping/serialization helpers.
9. Cron wiring: script entrypoint + что говорит ARCHITECTURE.md (не выдумывать schedule если не в репо — проверить `render.yaml` только если файл доступен в корне репо; если читаешь — ок, это ops факт).

## Обязательный контент

1. State diagram mermaid для BookingStatus (только подтверждённые переходами в коде).
2. Sequence: create pending booking (+ optional order).
3. Sequence: lifecycle expire.
4. Walkthrough **всех публичных** функций в:
   - `booking/service.py`
   - `booking/lifecycle.py`
   - `booking/policies.py`
   - `booking/order/service.py` (или аналог)
   - ключевые query/persistence helpers, если они часть публичного потока
5. Таблица HTTP routes booking + order + occurrence_bookings.
6. Явная секция «Граница с payment»: какие поля/статусы payment будет читать/менять (символы), без деталей Stripe.
7. 5+ checkpoint questions (включая capacity и expire).
8. What to watch out for: double booking, hold TTL, guest PII, transaction boundaries.

## DoD

- [ ] State transitions подтверждены кодом/тестами
- [ ] Lifecycle связан со script
- [ ] Нет выдуманных payment шагов
- [ ] Код не изменён

## Язык

Русский + точные символы.
