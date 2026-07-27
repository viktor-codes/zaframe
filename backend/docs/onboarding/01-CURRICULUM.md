# 01 — Curriculum: пошаговое погружение бэкендера

> Читай сверху вниз. Каждый шаг = гайд в `guides/` + практика «открой файл» + checkpoint.
> Не цель — запомнить API. Цель — **видеть поток управления и данные**.

## Метод чтения кода (использовать на каждом шаге)

1. **Снаружи внутрь:** HTTP route → schema → service → repository → model.
2. **По имени:** что делает символ? `create_*`, `ensure_*`, `confirm_*`, `expire_*`.
3. **По границам:** кто импортирует этот модуль? (смотреть `__init__.py` published API).
4. **По ошибкам:** какие `AppError` / status codes возможны?
5. **По тестам:** какой тест доказывает это поведение? (`tests/unit|integration|architecture`).
6. **По WHY:** ADR, комментарий `WHY:`, docstring lifespan/UoW — не выдумывать мотив.

---

## Шаг 0 — Ориентация (30–45 мин)

**Гайд:** `guides/00-inventory.md`  
**Зачем:** понять карту modular monolith до того, как читать домены.

Сделай сам:
- Открой `docs/ARCHITECTURE.md` и сравни с деревом `backend/app/modules/`.
- Открой `backend/app/modules/booking/__init__.py` — что экспортируется наружу?
- Запусти в уме: «куда нельзя импортировать из catalog?» (таблица allowed edges).

**Checkpoint:** раздел «Шаг 0» в `CHECKPOINTS.md`.

---

## Шаг 1 — Bootstrap приложения (45–60 мин)

**Гайд:** `guides/01-bootstrap.md`  
**Зачем:** любой запрос сначала проходит через app factory / middleware / router mount.

Сделай сам:
- Проследи: `main.py` → middleware → `register_routers` → конкретный `APIRouter`.
- Найди, где формируется Problem JSON / request id.
- Открой `GET /health` — что проверяется.

**Checkpoint:** «Шаг 1».

---

## Шаг 2 — Persistence: models → migrations → UoW → repository (90–120 мин)

**Гайд:** `guides/02-persistence.md`  
**Зачем:** без этого доменный код «висит в воздухе». Здесь рождается схема данных.

Сделай сам (важно — медленно):
1. Выбери одну сущность, например `Booking` (`app/models/booking.py`).
2. Найди поля, enum статусов, FK, индексы.
3. Найди миграции, которые их вводили (`alembic/versions/*booking*`, `*domain*`, …).
4. Найди repository-методы, которые читают/пишут эту модель.
5. Открой `UnitOfWork` + `uow_factory` + `uow_scope` / `get_uow` в deps.
6. Ответь: кто открывает транзакцию? кто делает `commit`?

**Checkpoint:** «Шаг 2».

---

## Шаг 3 — Контракты HTTP: schemas, DTO, pagination, errors (60 мин)

**Гайд:** `guides/03-contracts.md`  
**Зачем:** граница доверия. Всё внешнее валидируется здесь.

Сделай сам:
- Сравни request schema vs response schema на одном эндпоинте.
- Найди pagination envelope.
- Найди базовые исключения и как они мапятся в HTTP.

**Checkpoint:** «Шаг 3».

---

## Шаг 4 — Auth + Identity (90 мин)

**Гайд:** `guides/04-auth-identity.md`  
**Зачем:** почти все write-операции зависят от «кто я» и «какая роль в студии».

Сделай сам:
- Проследи OTP login → access JWT → refresh cookie.
- Найди `get_current_user` / optional user deps.
- Найди RBAC: `StudioMember`, policies, permission checks.
- Найди soft-delete / GDPR путь пользователя.

**Checkpoint:** «Шаг 4».

---

## Шаг 5 — Catalog: studio → service → schedule → occurrence (90–120 мин)

**Гайд:** `guides/05-catalog.md`  
**Зачем:** продукт, который потом бронируют. Иерархия сущностей критична.

Сделай сам:
- Нарисуй на бумаге: Studio 1—N Service 1—N Occurrence; ScheduleTemplate где стоит.
- Проследи создание occurrence / генерацию из schedule (если есть).
- Открой public vs owner routers — чем отличаются схемы ответа.

**Checkpoint:** «Шаг 5».

---

## Шаг 6 — Booking + Order + lifecycle (120 мин) — ядро продукта

**Гайд:** `guides/06-booking.md`  
**Зачем:** главный бизнес-флоу до оплаты.

Сделай сам:
- Проследи создание pending booking / hold.
- Найди capacity / uniqueness / guest attach.
- Проследи order creation (course vs single).
- Открой `lifecycle.py` + cron script — expire / complete.
- Найди policies: `is_own_booking` и кто их импортирует.

**Checkpoint:** «Шаг 6».

---

## Шаг 7 — Payment + Stripe (120 мин)

**Гайд:** `guides/07-payment.md`  
**Зачем:** деньги + идемпотентность webhooks + ledger.

Сделай сам:
- Checkout session creation → что пишется в Order/Payment.
- Webhook verify → processor → confirmation → capacity.
- Refund path (на уровне кода, не «как Stripe в теории»).
- Connect onboarding stubs / gates (`stripe_charges_enabled`).

**Checkpoint:** «Шаг 7».

---

## Шаг 8 — Search + ops + observability (45–60 мин)

**Гайд:** `guides/08-search-ops.md`  
**Зачем:** read-model и эксплуатация — иначе «почему в проде истекли холды?» непонятно.

Сделай сам:
- Search service/repository — какие таблицы читает.
- Scripts: booking lifecycle, OTP cleanup.
- Logging / metrics / rate limit — где включаются.

**Checkpoint:** «Шаг 8».

---

## Шаг 9 — Синтез: сквозные сценарии (60–90 мин)

**Гайд:** `guides/09-synthesis.md`  
**Зачем:** склеить голову. Доказать себе, что флоу целиком понятен.

Сценарии (пройти пальцем по коду end-to-end):

1. **Guest book → pay → confirm seats**
2. **Pending hold expires** (lifecycle cron)
3. **Studio owner manages catalog** (RBAC)
4. **Auth: OTP → refresh → /me**
5. **Webhook replay / idempotency** (`ProcessedWebhookEvent`)

**Checkpoint:** «Шаг 9» + финальный устный разбор с техлидом (или самопроверка по ключам).

---

## Рекомендуемый календарь

| День | Шаги |
|------|------|
| 1 | 0–2 |
| 2 | 3–5 |
| 3 | 6–7 |
| 4 | 8–9 + починить один маленький bug / написать один тест (после онбординга) |

---

## Что считать «я готов писать код»

Ты готов, если без подсказок можешь:

1. Назвать слой нового файла и куда его класть.
2. Добавить поле в модель + миграцию + schema + repository method по существующему паттерну.
3. Объяснить, почему `catalog` не импортирует `payment`.
4. Указать, где коммитится транзакция в типичном POST.
5. Найти тест, который сломается, если изменить статус booking неправильно.
