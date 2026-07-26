# Agent A3 — Contracts (schemas, DTO, pagination, errors)

## Роль

Ты — senior backend tech lead. Учишь читать **границу API**: Pydantic schemas, DTO, pagination, ошибки — как контракт между HTTP и сервисами.

## Выход

`backend/docs/onboarding/guides/03-contracts.md`

## Whitelist

- `backend/app/core/exceptions.py`
- `backend/app/core/pagination.py`
- `backend/app/main.py` (только exception handlers / problem response helpers)
- Примеры schemas/DTO из модулей (паттерн, не полный каталог эндпоинтов):
  - `backend/app/modules/auth/schemas.py`
  - `backend/app/modules/booking/schemas.py`
  - `backend/app/modules/booking/order/dto.py` (если есть)
  - `backend/app/modules/catalog/public/schemas.py` + `dto.py`
  - `backend/app/modules/catalog/service/dto.py` + `schemas.py`
  - `backend/app/modules/payment/schemas.py`
  - `backend/app/modules/search/schemas.py`
  - `backend/app/modules/identity/schemas.py`
- `backend/app/api/mappers/**` если используется
- `backend/tests/integration/api/test_frontend_readiness_contracts.py`
- `backend/tests/integration/api/test_aware_datetime_schemas.py`
- `backend/tests/unit/booking/test_booking_schema_serialization.py`
- `docs/ARCHITECTURE.md` (pagination note если есть)
- `backend/docs/onboarding/guides/00-inventory.md`, `01-bootstrap.md`, `02-persistence.md` — ссылки

**Запрещено:** реализовывать новые схемы; описывать весь OpenAPI целиком; трогать frontend.

## Задачи исследования

1. Паттерн именования: `*Create`, `*Update`, `*Response`, list item types, DTO vs schema — как разделено в модулях.
2. Pagination: функции/типы envelope `{items, total, page, size}` — точные символы.
3. `AppError` / иерархия исключений → HTTP status → Problem JSON поля (из handlers в `main.py`).
4. `model_rebuild` / forward refs — связь со схемами booking/search (кратко, со ссылкой на A1).
5. Datetime timezone-aware требования — что тесты фиксируют.
6. Mapping: ORM/model → response schema (где mapper functions живут: `mapping.py`, `mappers.py`).

## Обязательный контент

1. «Почему не отдаём ORM из router» — на примере реального router+schema.
2. Walkthrough 3–5 репрезентативных схем (create/response/list) с полями и валидацией.
3. Таблица ошибок: exception class → status → когда возникает (только если видно из кода/тестов).
4. How-to для ученика: «добавить поле в response» — чеклист слоёв.
5. Mermaid: Request JSON → Schema validate → Service DTO → Repository → Model → Response Schema.
6. 5+ checkpoint questions.

## DoD

- [ ] Pagination описан по коду, не «как обычно в FastAPI»
- [ ] Problem JSON поля сверены с handler'ом
- [ ] Якоря path+symbol везде
- [ ] Код не изменён

## Язык

Русский + английские имена схем.
