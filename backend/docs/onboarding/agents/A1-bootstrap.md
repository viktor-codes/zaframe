# Agent A1 — Bootstrap (main, middleware, routers)

## Роль

Ты — senior backend tech lead. Пишешь гайд о том, **как приложение поднимается и как HTTP-запрос входит в систему** до доменного service.

## Выход

`backend/docs/onboarding/guides/01-bootstrap.md`

Каркас — из `backend/docs/onboarding/00-ORCHESTRATION.md`.

## Whitelist

- `backend/app/main.py`
- `backend/app/api/` (`router.py`, `health.py`, `metrics.py`, mappers если есть)
- `backend/app/core/config.py`
- `backend/app/core/database.py`
- `backend/app/core/logging_config.py`
- `backend/app/core/middleware/`
- `backend/app/core/exceptions.py`
- `backend/app/core/rate_limit.py`
- `backend/app/core/observability.py`
- `backend/app/core/deps.py` (только обзор: какие deps существуют — без глубокого auth)
- `backend/.env.example` (имена переменных, без секретов)
- `docs/ARCHITECTURE.md` (health / production notes — только если нужно)
- `backend/docs/onboarding/guides/00-inventory.md` (если уже есть — ссылайся, не дублируй)

**Запрещено:** бизнес-логика booking/payment, детали OTP, изменение кода.

## Задачи исследования

1. Разбери `main.py`: создание FastAPI, lifespan, CORS, security headers, exception handlers, rate limit handler.
2. Проследи `register_routers`: какие routers входят в `/api/v1`, что снаружи (health, metrics, webhooks).
3. Объясни `model_rebuild()` в `api/router.py` — зачем, на каких схемах.
4. Request logging / request id middleware: где генерируется, куда кладётся, какой header.
5. Health endpoint: что возвращает, проверка DB.
6. Settings (`config.py`): паттерн загрузки, что критично для prod (без копирования секретов).

## Обязательный контент

1. Sequence mermaid: `Client → Middleware → Router → Depends(get_uow/user) → Service` (на уровне bootstrap, не конкретного домена).
2. Walkthrough **каждой** публичной функции/класса в `main.py`, имеющих отношение к request path (middleware class, lifespan, handlers).
3. Таблица: middleware / handler | файл | зачем.
4. How-to: «добавить новый router в api_v1» — шаги по существующему паттерну.
5. 5+ checkpoint questions.
6. What to watch out for: docs paths vs CSP, production HSTS, docs не утекают ли лишнее.

## DoD

- [ ] `guides/01-bootstrap.md` готов по шаблону
- [ ] Каждый факт с якорем path+symbol
- [ ] Нет выдуманных env vars — только из `.env.example` / Settings полей
- [ ] Код не изменён

## Язык

Русский + английские идентификаторы.
