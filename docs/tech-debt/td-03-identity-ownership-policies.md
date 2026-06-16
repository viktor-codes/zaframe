# TD-03 — Unify guest/user ownership policies (P1)

> Read [README.md](./README.md).

## Problem

Identical ownership logic exists in two places:

```python
# booking/policies.py
def is_own_booking(booking, user) -> bool:
    # user_id match OR guest_email.lower() == user.email.lower()

# payment/service.py (or payment/access.py after td-02)
def is_own_order(order, user) -> bool:
    # same pattern
```

Future identity rules (phone match, normalized email, merged accounts) would require dual edits.

## Goal

One canonical policy in `identity` (leaf module, no upstream deps). Booking and payment
import the shared helper.

## Target

```
app/modules/identity/policies.py   # NEW
```

```python
def is_owned_by_user(
    *,
    user: User,
    user_id: int | None,
    guest_email: str | None,
) -> bool:
    """True when resource is linked by user_id or guest_email (case-insensitive)."""

def is_own_booking(booking: Booking, user: User) -> bool:
    return is_owned_by_user(user=user, user_id=booking.user_id, guest_email=booking.guest_email)

def is_own_order(order: Order, user: User) -> bool:
    return is_owned_by_user(user=user, user_id=order.user_id, guest_email=order.guest_email)
```

**Decision:** keep `is_own_booking` in `booking/policies.py` as a thin wrapper that calls
`identity.policies.is_owned_by_user` — preserves the published `booking` API for `payment`.
Move `is_own_order` to `payment/access.py` (or keep in payment) as wrapper — **do not**
export `is_own_order` from `identity/__init__.py` unless needed.

### Preferred approach (minimal API churn)

`identity/policies.py` exports only:
- `is_owned_by_user(...)`

`booking/policies.py`:
```python
from app.modules.identity.policies import is_owned_by_user

def is_own_booking(booking, user):
    return is_owned_by_user(user=user, user_id=booking.user_id, guest_email=booking.guest_email)
```

`payment` (access.py or service.py):
```python
def is_own_order(order, user):
    return is_owned_by_user(user=user, user_id=order.user_id, guest_email=order.guest_email)
```

`can_access_booking` stays in `booking/policies.py` (booking-specific studio owner rule).

## import-linter impact

New edge: `booking → identity` and `payment → identity`.

- `booking → identity` — **already allowed** (booking may import identity).
- `payment → identity` — **currently forbidden** (`payment only reaches booking`).

### Required contract update in `pyproject.toml`

```toml
[[tool.importlinter.contracts]]
name = "payment only reaches booking and identity (not catalog/auth)"
type = "forbidden"
source_modules = ["app.modules.payment"]
forbidden_modules = ["app.modules.catalog", "app.modules.auth"]
# identity import is allowed — do NOT add identity to forbidden_modules
```

Rename contract description only; behaviour widens intentionally.

Update `docs/ARCHITECTURE.md` allowed-edges table:
`| payment | booking, identity, core, models, integrations |`

## Tests

Add `tests/unit/test_identity_policies.py`:

| Case | Expected |
|------|----------|
| `user_id` matches | True |
| `guest_email` matches (case insensitive) | True |
| neither matches | False |
| both None | False |

Existing `test_payment_service.py`, booking authz tests — unchanged behaviour.

## Definition of Done

- Zero duplicate email/user_id comparison blocks outside `identity/policies.py`.
- `uv run lint-imports` KEPT (with updated contract name/docs).
- `uv run pytest -q` 172+ passed.

## Commit

```
refactor(identity): add is_owned_by_user policy shared by booking and payment
```

## Out of scope

Phone-based ownership; studio-owner access (stays in booking).
