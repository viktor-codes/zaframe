# TZ-03 — Extract `identity` (User) into `modules/identity`

> Read [README.md](./README.md). `identity` = the User entity's repository, service, schemas.

## Goal & why
`User` is core domain referenced by studio/booking/order. Its *behaviour* (lookup,
get-or-create) is separate from the auth *process* (OTP/JWT). Splitting them keeps `auth`
from becoming a dependency hub (SRP, ADR-003 §3.2). `User` the **ORM model stays in
`app/models/user.py`** (README §3).

> **No router this step.** There is no standalone users router today; the only user-facing
> endpoint is `GET /auth/me`, which is session-bound and stays in the auth router (tz-04).
> So `modules/identity` has no `router.py`.

## Preconditions
- Branch `refactor/modular-monolith`, tests green.

## Files (`git mv`)
| From | To |
|------|----|
| `app/services/user.py` | `app/modules/identity/service.py` |
| `app/repositories/user_repo.py` | `app/modules/identity/repository.py` |
| `app/schemas/user.py` | `app/modules/identity/schemas.py` |
| _(new)_ | `app/modules/identity/__init__.py` |

## Steps
1. `git mv` the three files; create `__init__.py`.
2. In-file imports:
   - `service.py`: keep `from app.core.uow import UnitOfWork`, `from app.models.user import User`.
   - `repository.py`: keep `app.models`, `app.repositories.base`.
   - `schemas.py`: keep as-is.
3. Published interface — `app/modules/identity/__init__.py`:
   ```python
   from app.modules.identity.repository import UserRepository
   from app.modules.identity.schemas import UserCreate, UserPublic, UserResponse, UserUpdate
   from app.modules.identity.service import (
       get_or_create_user,
       get_user_by_email,
       get_user_by_id,
   )

   __all__ = [
       "UserRepository",
       "UserCreate", "UserUpdate", "UserResponse", "UserPublic",
       "get_or_create_user", "get_user_by_email", "get_user_by_id",
   ]
   ```
4. Schema facade — `app/schemas/__init__.py`: re-export the User schemas from
   `app.modules.identity.schemas`. Keep `__all__` names. **Keep** the
   `UserResponse.model_rebuild()`-related ordering if any (none specific to User today).
5. Repo wiring — `app/repositories/__init__.py` and `core/uow.py`: import `UserRepository`
   from `app.modules.identity`. Attribute `uow.users` unchanged.
6. **Do not** repoint `services/auth.py` yet — it currently does
   `from app.services.user import get_or_create_user, get_user_by_id`. This keeps working via
   the `app/services/__init__.py`/module path? **No** — `services/auth.py` imports the module
   directly. To keep it green, add a thin facade: leave a re-export shim
   `app/services/user.py` is gone, so instead update `services/auth.py` import line to
   `from app.modules.identity import get_or_create_user, get_user_by_id`. (This one-line edit
   in auth is allowed here; auth's full move is tz-04.)

## Grep targets
```bash
rg -n "app\.services\.user|app\.repositories\.user_repo|app\.schemas\.user" backend
```
Allowed: none (auth now imports from `app.modules.identity`).

## Definition of Done
`uv run ruff check . && uv run lint-imports && uv run pytest -q` → 170 passed.

## Commit
```
refactor(identity): extract identity (User) into modules/identity
```

## Out of scope
Auth move, `/me` endpoint, User ORM model.
