# TD-09 — Pyright strict in dev + CI (P3)

> Read [README.md](./README.md).

## Problem

Typing relies on Ruff (`F` rules) but not on strict static analysis. `UnitOfWork` uses
`Any` for repository attributes; lazy `__getattr__` in module `__init__.py` files hides
missing exports. Regressions slip through until runtime.

## Goal

Add **Pyright** in strict mode for `app/` and `scripts/`, integrated into `make lint` and
CI. Zero errors on baseline — fix real issues, use narrow `pyrightconfig` exclusions only
where justified (document WHY).

## Steps

### 1. Add dependency

```bash
cd backend && uv add --dev pyright
```

### 2. Configure `backend/pyproject.toml` or `pyrightconfig.json`

Recommended in `pyproject.toml`:

```toml
[tool.pyright]
pythonVersion = "3.13"
typeCheckingMode = "strict"
include = ["app", "scripts", "tests"]
exclude = [".venv", "alembic/versions"]
reportMissingTypeStubs = false
# sqlalchemy stubs optional: types-sqlalchemy later
```

### 3. Fix `UnitOfWork` typing (high value)

Replace `Any` repos in `core/uow.py` with explicit types using **TYPE_CHECKING** to avoid
import cycles:

```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.modules.booking.repository import BookingRepository
    ...

@dataclass
class UnitOfWork:
    session: AsyncSession
    bookings: BookingRepository
    ...
```

`uow_factory.py` remains the runtime wiring point — no cycle if `uow.py` only TYPE_CHECKING
imports repos.

### 4. Triage errors incrementally

Suggested order:
1. `core/` (uow, deps, config)
2. `modules/identity`, `search` (leaves)
3. `modules/booking`, `payment`, `catalog`
4. `tests/` — may use `reportUnknownMemberType = false` for tests only via
   `exclude` or per-file override

**Do not** blanket `# pyright: ignore` on files. Per-line only with comment WHY.

### 5. Makefile

```makefile
lint:
	cd backend && uv run ruff check .
	cd backend && uv run lint-imports
	cd backend && uv run pyright
```

### 6. CI

If GitHub Actions exists, add pyright step to lint job. If no CI yet, document in
`docs/ARCHITECTURE.md` local command only.

## Known hard spots (plan before coding)

| Area | Issue | Mitigation |
|------|-------|------------|
| SQLAlchemy ORM | Column types | `Mapped[]` already used; may need `sqlalchemy2-stubs` |
| Lazy `__getattr__` in `__init__.py` | pyright doesn't see exports | Add explicit imports in `TYPE_CHECKING` block + `__all__` |
| FastAPI `Depends()` | B008 ignored in Ruff | pyright may need annotated deps |

Optional: `uv add --dev types-passlib` etc. only if errors warrant it — ask user before
adding many stub packages.

## Tests

`uv run pyright` exit code 0.

Existing pytest suite unchanged.

## Definition of Done

- `uv run pyright` — 0 errors in `app/`.
- `make lint` includes pyright.
- `docs/ARCHITECTURE.md` updated in Running checks section.

## Commit

```
chore(api): add pyright strict checking to lint pipeline
```

## Out of scope

Mypy; typing every test helper; frontend `tsc` changes (separate task).
