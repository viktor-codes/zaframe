# TZ-11 — Architecture guards: enforce module boundaries

> Read [README.md](./README.md). Depends on tz-10 (final layout in place). Low risk.

## Goal & why
Make the new boundaries self-enforcing so they survive team growth (ADR-003 §5). Without
guards, the next "quick import" silently rebuilds the coupling we just removed.

## Part A — Tighten `import-linter` contracts (in `pyproject.toml`)
Replace the Phase-0 placeholder contracts with the final set. Keep `root_package = "app"`.

1. **Core stays infrastructure (UoW is the only wiring exception).**
   ```toml
   [[tool.importlinter.contracts]]
   name = "Core infra does not import modules"
   type = "forbidden"
   source_modules = [
     "app.core.config", "app.core.security", "app.core.exceptions",
     "app.core.datetime_utils", "app.core.database", "app.core.repository",
   ]
   forbidden_modules = ["app.modules"]
   ```
   (`app.core.uow` is intentionally allowed to import module repositories.)

2. **Models hold no logic dependencies.**
   ```toml
   [[tool.importlinter.contracts]]
   name = "Models import nothing but core"
   type = "forbidden"
   source_modules = ["app.models"]
   forbidden_modules = ["app.modules", "app.api"]
   ```

3. **Domain independence (allowed edges only).** Add one `forbidden` contract per banned
   direction. Allowed edges (do NOT ban): `booking → catalog`, `payment → booking`,
   `auth → {booking, identity}`, any `→ integrations`, any `→ core/models`. Ban the rest, e.g.:
   ```toml
   [[tool.importlinter.contracts]]
   name = "catalog does not depend on booking/payment/auth"
   type = "forbidden"
   source_modules = ["app.modules.catalog"]
   forbidden_modules = ["app.modules.booking", "app.modules.payment", "app.modules.auth"]

   [[tool.importlinter.contracts]]
   name = "identity is a leaf"
   type = "forbidden"
   source_modules = ["app.modules.identity"]
   forbidden_modules = ["app.modules.auth", "app.modules.booking", "app.modules.catalog", "app.modules.payment", "app.modules.search"]

   [[tool.importlinter.contracts]]
   name = "search is read-only leaf"
   type = "forbidden"
   source_modules = ["app.modules.search"]
   forbidden_modules = ["app.modules.booking", "app.modules.catalog", "app.modules.payment", "app.modules.auth"]

   [[tool.importlinter.contracts]]
   name = "payment only reaches booking (not catalog/auth)"
   type = "forbidden"
   source_modules = ["app.modules.payment"]
   forbidden_modules = ["app.modules.catalog", "app.modules.auth"]
   ```

4. **API layer is top.**
   ```toml
   [[tool.importlinter.contracts]]
   name = "Nothing imports the API layer"
   type = "forbidden"
   source_modules = ["app.modules", "app.core", "app.models"]
   forbidden_modules = ["app.api"]
   ```

Run `uv run lint-imports` — all KEPT. If a contract breaks, it means a real boundary
violation slipped in during tz-01…tz-10; fix the import, do not relax the contract.

## Part B — Boundary unit test (`tests/architecture/test_boundaries.py`)
AST-based, no DB. Covers what import-linter can't express ergonomically:

1. `test_repository_files_have_no_service_or_router_imports` — walk every
   `app/modules/**/repository.py`; assert no import of `service`, `router`, `policies`.
2. `test_no_private_cross_domain_imports` — walk every `app/modules/**/*.py`; for each
   `from app.modules.<other_domain>... import _name`, assert the imported names do not start
   with `_` unless `<other_domain>` equals the file's own top-level domain.

Add `tests/architecture/__init__.py`. Keep these tests fast (pure AST, parse files via
`ast.parse`).

## Part C — Docs
1. `docs/ARCHITECTURE.md` (or `backend/docs/`): final tree, the dependency-direction rule
   (`router → service → repository → core/models`), the allowed cross-domain edges table
   (mirror Part A item 3), and a Mermaid module graph.
2. Update `docs/refactor/README.md` status to "completed"; tick the ADR-003 phases.

## Part D — CI wiring
Add `uv run lint-imports` to the lint step of CI (and the `Makefile` `lint` target if one
exists; otherwise create the `lint` target running ruff + lint-imports). It must fail the
build on a broken contract.

## Definition of Done
- `uv run ruff check . && uv run lint-imports && uv run pytest -q` → green (172+ tests:
  170 existing + new boundary tests).
- A deliberate violation (temporary edit) makes BOTH `lint-imports` and `test_boundaries`
  fail — verify, then revert.

## Commit
```
test(api): enforce module boundaries via import-linter + test_boundaries
```
