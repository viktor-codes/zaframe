# Agent A7 — Payment + Stripe + Webhooks

## Роль

Ты — senior backend tech lead. Объясняешь деньги: checkout, Connect gates, webhook idempotency, confirmation seats, ledger/manual_review, refunds — строго по коду модулей payment + integrations/stripe.

## Выход

`backend/docs/onboarding/guides/07-payment.md`

## Whitelist

- `backend/app/modules/payment/**`
- `backend/app/integrations/stripe/**`
- Models: `payment.py`, `processed_webhook_event.py`, связанные поля `order.py` / `studio.py` (stripe fields)
- Migrations: `004_processed_webhook_events.py`, `012_stripe_connect_payment_ledger.py`, `015_order_checkout_session_id.py`
- Tests:
  - `backend/tests/unit/payment/**`
  - `backend/tests/integration/api/test_webhooks.py`
  - `backend/tests/integration/repositories/test_payment_confirm_queries.py`
- Booking **только** published API, используемый payment (confirmation/capacity) — ссылка на guide 06 для booking internals
- `docs/ARCHITECTURE.md` (Connect fee deferred, manual_review note)
- Guides 02/06 for links

**Запрещено:** менять код; «как работает Stripe вообще» без привязки к нашим функциям; выдумывать fee model если в ARCHITECTURE сказано deferred.

## Задачи исследования

1. Разложи файлы payment: `service.py` (фасад?) vs `checkout.py`, `webhooks.py`, `webhook_processor.py`, `confirmation.py`, `capacity.py`, `ledger.py`, `refunds.py`, `connect.py`, `access.py`, `stripe_client.py`.
2. HTTP: payment router + studio_payment_router + webhooks router (mount вне `/api/v1` — сверить `api/router.py`).
3. Checkout creation: входы, запись Order/Payment, вызов integrations/stripe.
4. Webhook: signature verify → idempotency via ProcessedWebhookEvent → processor branches.
5. Confirmation path: как seats подтверждаются, что если нельзя безопасно confirm → `manual_review` (найти в коде).
6. Refunds path.
7. Connect onboarding / `stripe_charges_enabled` gates.
8. Ledger semantics — по коду/миграции 012.
9. Published interface payment module.

## Обязательный контент

1. Sequence mermaid: checkout → Stripe → webhook → confirm.
2. Sequence mermaid: duplicate webhook (idempotency).
3. Sequence mermaid: late payment after hold expired (если код это обрабатывает; иначе UNKNOWN + open question).
4. Walkthrough публичных функций по файлам payment (сгруппируй: если service — тонкий фасад, укажи делегирование).
5. Таблица PaymentStatus / RefundStatus / Order status interactions.
6. Граница `integrations/stripe` (IO) vs `modules/payment` (domain rules).
7. 5+ checkpoint questions.
8. What to watch out for: idempotency keys, signature secrets via env, never log payloads with PII/secrets, Connect not ready.

## DoD

- [ ] Webhook path полностью прослежен с якорями
- [ ] manual_review объяснён только если есть в коде
- [ ] Нет выдуманной fee logic
- [ ] Код не изменён

## Язык

Русский + точные символы.
