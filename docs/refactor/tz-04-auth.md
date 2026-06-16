# TZ-04 — Move `auth` into `modules/auth`; `email` into `integrations`

> Read [README.md](./README.md). Depends on **tz-03** (identity).

## Goal & why
`auth` owns the sign-in process: OTP, refresh-token sessions, login, JWT. It legitimately
**orchestrates** identity + booking + email — allowed, but only via published interfaces
(README §5). `email` is an external adapter, so it moves to `integrations/`.

## Preconditions
- tz-03 merged (identity exists). Tests green.

## Files (`git mv`)
| From | To |
|------|----|
| `app/services/auth.py` | `app/modules/auth/service.py` |
| `app/schemas/auth.py` | `app/modules/auth/schemas.py` |
| `app/api/v1/auth.py` | `app/modules/auth/router.py` |
| `app/repositories/otp_code_repo.py` | `app/modules/auth/repository.py` (OTPCodeRepository) |
| `app/repositories/refresh_token_repo.py` | merge into `app/modules/auth/repository.py` **or** keep as `app/modules/auth/refresh_repository.py` |
| `app/services/email.py` | `app/integrations/email/service.py` |
| _(new)_ | `app/modules/auth/__init__.py`, `app/integrations/email/__init__.py` |

> Decision: put both `OTPCodeRepository` and `RefreshTokenRepository` in one
> `modules/auth/repository.py` (they share the auth domain). If you prefer two files, keep
> names importable from `modules/auth/__init__.py` regardless.

## Steps
1. Move email first: `git mv app/services/email.py app/integrations/email/service.py`;
   `app/integrations/email/__init__.py`:
   ```python
   from app.integrations.email.service import send_otp_email
   __all__ = ["send_otp_email"]
   ```
2. `git mv` the auth files and the two repo files into `modules/auth/`.
3. In-file imports in `modules/auth/service.py`:
   - keep `from app.core.security import ...`, `from app.core.uow import UnitOfWork`, `from app.models...`.
   - `from app.services.email import send_otp_email` → `from app.integrations.email import send_otp_email`.
   - `from app.services.user import ...` → `from app.modules.identity import get_or_create_user, get_user_by_id`.
   - **Leave** `from app.services.booking import attach_guest_bookings` (booking not moved until tz-09; temporary, README §5).
4. `modules/auth/router.py` imports:
   - `from app.services.auth import ...` → `from app.modules.auth.service import ...`.
   - `from app.schemas.auth import ...` → `from app.modules.auth.schemas import ...`.
   - `from app.schemas.user import UserResponse` → `from app.modules.identity import UserResponse`.
   - keep `app.api.deps`, `app.core.*`.
5. `repository.py`: keep `app.models`, `app.repositories.base`.
6. Published interface — `app/modules/auth/__init__.py`:
   ```python
   from app.modules.auth.repository import OTPCodeRepository, RefreshTokenRepository
   from app.modules.auth.service import get_current_user_from_token

   __all__ = ["OTPCodeRepository", "RefreshTokenRepository", "get_current_user_from_token"]
   ```
7. Wiring:
   - `core/uow.py`: import `OTPCodeRepository`, `RefreshTokenRepository` from `app.modules.auth`. Attributes `uow.otp_codes`, `uow.refresh_tokens` unchanged.
   - `app/repositories/__init__.py`: re-export both from `app.modules.auth`.
   - `app/schemas/__init__.py`: auth schemas have no entries in the central aggregator today — verify; if absent, nothing to change.
   - `app/api/deps.py`: `from app.services.auth import get_current_user_from_token` → `from app.modules.auth import get_current_user_from_token`.
   - `app/main.py`: remove `auth` from `from app.api.v1 import (...)`; add `from app.modules.auth.router import router as auth_router`; keep its `include_router(..., prefix="/api/v1")`.
8. **Tests (critical):**
   - `backend/tests/conftest.py` line ~109: `patch("app.services.auth.send_otp_email", ...)` → `patch("app.modules.auth.service.send_otp_email", ...)`.
   - `backend/tests/unit/test_email_logging.py`: repoint `app.services.email` → `app.integrations.email.service`.
   - `backend/tests/test_auth_service.py`, `test_api_auth.py`: repoint any `app.services.auth` patches/imports → `app.modules.auth.service`.

## Grep targets
```bash
rg -n "app\.services\.auth|app\.services\.email|app\.schemas\.auth|app\.repositories\.(otp_code_repo|refresh_token_repo)|app\.api\.v1\.auth" backend
```
Allowed: only `from app.services.booking import attach_guest_bookings` in
`modules/auth/service.py` (temporary).

## Definition of Done
`uv run ruff check . && uv run lint-imports && uv run pytest -q` → 170 passed (auth tests
included).

## Commit
```
refactor(auth): move auth into modules/auth; email into integrations
```

## Out of scope
booking move; `/me` stays in auth router.
