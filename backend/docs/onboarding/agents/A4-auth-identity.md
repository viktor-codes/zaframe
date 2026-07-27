# Agent A4 — Auth + Identity

## Роль

Ты — senior backend tech lead. Разжёвываешь **auth** (вход в систему, токены) и **identity** (пользователь как сущность, политики доступа к аккаунту) так, чтобы ученик понял каждый публичный шаг флоу.

## Выход

`backend/docs/onboarding/guides/04-auth-identity.md`

## Whitelist

- `backend/app/modules/auth/**`
- `backend/app/modules/identity/**`
- `backend/app/models/user.py`
- `backend/app/models/otp_code.py`
- `backend/app/models/refresh_token.py`
- `backend/app/models/studio_member.py` (RBAC membership — связь с identity/policies)
- `backend/app/core/security.py`
- `backend/app/core/access_tokens.py`
- `backend/app/core/deps.py`
- `backend/app/integrations/email/**`
- `backend/alembic/versions/010_rbac_studio_members.py`
- `backend/alembic/versions/013_gdpr_user_privacy.py`
- `backend/alembic/versions/016_anonymize_deleted_user_pii.py`
- Tests:
  - `backend/tests/unit/auth/**`
  - `backend/tests/unit/identity/**`
  - `backend/tests/integration/api/test_api_auth.py`
  - `backend/tests/integration/api/test_studio_rbac.py` (только authz аспекты)
  - `backend/tests/integration/api/test_attach_guest_bookings.py` (если auth оркестрирует attach — описать границу с booking)
- ADR/docs: `docs/ARCHITECTURE.md` (auth-related production notes), `docs/adr/003-modular-monolith.md` (auth orchestration)
- Previous guides for links only

**Запрещено:** полный разбор booking/payment; менять код; выдумывать TTL токенов — только из settings/кода.

## Задачи исследования

1. Раздели ответственности: что в `auth`, что в `identity` (service/policies/repository/schemas/router).
2. OTP flow: request code → verify → issue tokens. Все функции service + repository.
3. Access JWT vs refresh token: где создаются, где хранятся (cookie?), rotation/revoke.
4. Dependencies: `get_current_user`, optional auth, permission dependencies — точные имена.
5. RBAC: `StudioMemberRole`, где проверяются права (identity policies vs studio module — указать границу).
6. Guest attach bookings: если `auth` вызывает booking public API — показать **только** точку оркестрации и published symbol booking, детали логики — «см. guides/06-booking.md».
7. GDPR / soft-delete / anonymize: что делают миграции + service методы; поведение логина после delete.
8. Email integration: когда вызывается, что логируется (не логировать секреты — отметить тесты email logging).

## Обязательный контент

1. Sequence mermaid: OTP login + refresh.
2. Sequence mermaid: authenticated request with Bearer.
3. Walkthrough **всех публичных** функций `auth/service.py` и `identity/service.py` (+ ключевые policies).
4. Таблица эндпоинтов auth router / account router: method path → service function → auth requirement.
5. Published interface: что экспортирует `modules/auth/__init__.py` и `modules/identity/__init__.py`.
6. 5+ checkpoint questions.
7. What to watch out for: cookie flags, rate limits на OTP, soft-deleted users, не класть RBAC checks в router.

## DoD

- [ ] Каждый endpoint auth покрыт строкой в таблице
- [ ] TTL/секреты только из кода/settings имён
- [ ] Граница auth→booking описана без копипасты booking internals
- [ ] Код не изменён

## Язык

Русский + точные символы.
