# Agent A8 — Search + Ops + Observability

## Роль

Ты — senior backend tech lead. Закрываешь «хвосты», без которых бэкендер не оперирует системой: search read-model, cron/scripts, logging/metrics/rate-limit, health в проде.

## Выход

`backend/docs/onboarding/guides/08-search-ops.md`

## Whitelist

- `backend/app/modules/search/**`
- `backend/scripts/**` (все job entrypoints)
- `backend/app/core/logging_config.py`
- `backend/app/core/observability.py`
- `backend/app/core/rate_limit.py`
- `backend/app/core/middleware/**`
- `backend/app/api/health.py`
- `backend/app/api/metrics.py`
- `backend/app/main.py` (только куски rate limit / logging / middleware — не дублировать весь A1)
- `docs/ARCHITECTURE.md` (Background jobs, Production Readiness Notes)
- Root ops files **если существуют**: `render.yaml`, root `Makefile` targets связанные с backend (`booking-lifecycle`, `dev-api`, …)
- Tests: `backend/tests/unit/core/test_logging_observability.py` и любые search tests если есть
- Guides 00/01 for links

**Запрещено:** переписывать bootstrap гайд целиком; доменный payment/booking разбор; менять код.

## Задачи исследования

1. Search module: router/service/repository/schemas — что ищет, какие таблицы, leaf constraints.
2. Все scripts: назначение, идемпотентность, как запускать локально (`uv run` / make).
3. OTP cleanup: python script vs `pg_cron` sql — что актуально по ARCHITECTURE + файлам.
4. Rate limiting: slowapi + Redis dependency note.
5. Observability: structlog fields, request_id, metrics endpoint output.
6. Health checks: DB down → 503?
7. Production readiness bullets из ARCHITECTURE — только те, что проверяются наличием settings/code.

## Обязательный контент

1. Таблица jobs: name | entrypoint | schedule (если известен из repo) | side effects | idempotent?
2. Walkthrough search public functions + lifecycle script main.
3. Mermaid: cron → script → uow_scope → lifecycle functions (booking) — со ссылкой на guide 06.
4. How-to: «добавить новый cron script» по паттерну существующего.
5. 5+ checkpoint questions.
6. What to watch out for: multi-instance rate limit without Redis; missing cron → holds never expire.

## DoD

- [ ] Все scripts в `backend/scripts/` упомянуты или явно помечены non-job helpers
- [ ] Search описан как read-only leaf
- [ ] Код не изменён

## Язык

Русский + точные символы.
