# TZ-02 — Move `payment` (+ Stripe webhooks) into `modules/payment`

> Read [README.md](./README.md) and skim [tz-01](./tz-01-search.md) for the pattern.

## Goal & why
Co-locate payment service, its webhook router, schemas, and the only repository it *owns*
(`ProcessedWebhookEventRepository`). Payment **reads** Order/Booking/Occurrence via `uow`
but does not own those repos — leave them where they are.

## Preconditions
- Branch `refactor/modular-monolith`, tests green.

## Files (`git mv`)
| From | To |
|------|----|
| `app/services/payment.py` | `app/modules/payment/service.py` |
| `app/schemas/payment.py` | `app/modules/payment/schemas.py` |
| `app/api/v1/payments.py` | `app/modules/payment/router.py` |
| `app/api/webhooks.py` | `app/modules/payment/webhooks.py` |
| `app/repositories/processed_webhook_event_repo.py` | `app/modules/payment/repository.py` |
| _(new)_ | `app/modules/payment/__init__.py` |

## Steps
1. `git mv` the files; create `app/modules/payment/__init__.py`.
2. In-file imports:
   - `service.py`: keep `from app.integrations.stripe.checkout import ...`, `from app.models...`, `from app.core...`. Update self-reference to schemas: `from app.modules.payment.schemas import validate_checkout_redirect_urls`. **Leave** `from app.services.booking import is_own_booking` untouched (fixed in tz-09 — see README §5).
   - `router.py`: `from app.services.payment import ...` → `from app.modules.payment.service import ...`. Keep `app.api.deps`, `app.schemas` (facade), mappers.
   - `webhooks.py`: `from app.services.payment import confirm_booking_after_payment, confirm_order_after_payment` → `from app.modules.payment.service import ...`. Keep `app.core.uow`, `app.core.middleware...`.
   - `repository.py`: keep `app.models`, `app.repositories.base`.
3. Published interface — `app/modules/payment/__init__.py`:
   ```python
   from app.modules.payment.repository import ProcessedWebhookEventRepository

   __all__ = ["ProcessedWebhookEventRepository"]
   ```
4. Schema facade — `app/schemas/__init__.py`: re-export payment schemas from new path
   (`from app.modules.payment.schemas import CheckoutSessionCreate, CheckoutSessionResponse, OrderCheckoutSessionCreate`). Keep `__all__` names.
5. Repo wiring:
   - `app/repositories/__init__.py`: `ProcessedWebhookEventRepository` now imported from `app.modules.payment`.
   - `core/uow.py`: import `ProcessedWebhookEventRepository` from `app.modules.payment`. Attribute `uow.webhook_events` unchanged.
6. Router wiring — `app/main.py`:
   - remove `payments` from `from app.api.v1 import (...)`;
   - replace `from app.api.webhooks import router as webhooks_router` with
     `from app.modules.payment.webhooks import router as webhooks_router`;
   - add `from app.modules.payment.router import router as payments_router`;
   - keep both `include_router` calls (paths unchanged: payments under `/api/v1`, webhooks at root).
7. **conftest / tests:** check `backend/tests/test_webhooks.py` and integration payment tests
   for patch paths like `app.api.webhooks...` or `app.services.payment...` and repoint to
   `app.modules.payment.webhooks` / `app.modules.payment.service`.

## Grep targets
```bash
rg -n "app\.services\.payment|app\.api\.v1\.payments|app\.api\.webhooks|app\.schemas\.payment|app\.repositories\.processed_webhook_event_repo" backend
```
Allowed: only the deliberate `from app.services.booking import is_own_booking` inside
`modules/payment/service.py` (temporary, see README §5).

## Definition of Done
`uv run ruff check . && uv run lint-imports && uv run pytest -q` → 170 passed.

## Commit
```
refactor(payment): move payment + stripe webhooks into modules/payment
```

## Out of scope
Order/Booking/Occurrence repositories; `is_own_booking` promotion (tz-09).
