# Checkpoints — проверка понимания

> Отвечай **своими словами**, указывая файлы/символы.
> Правильные ответы появятся в `<details>` после того, как A9 (или Orchestrator) заполнит ключи.
> Пока гайды не готовы — используй эти вопросы как самопроверку после чтения кода.

---

## Шаг 0 — Inventory

1. Какие домены лежат в `app/modules/` и какой из них «лист» (leaf)?
2. Почему ORM-модели централизованы в `app/models/`, а не разложены по модулям? (источник: ADR)
3. Что такое published interface модуля и где он живёт?
4. Какая зависимость запрещена: `catalog → booking` или `booking → catalog`?
5. Чем `import-linter` отличается от `tests/architecture/`?

<details>
<summary>Ключи (заполняет A9 / Orchestrator)</summary>

- TODO after guides exist

</details>

---

## Шаг 1 — Bootstrap

1. Что происходит при старте и при остановке приложения (`lifespan`)?
2. Какие security headers выставляются всегда, какие — только в production?
3. Где монтируются `/api/v1` роутеры и отдельно webhooks?
4. Зачем в `api/router.py` вызывается `model_rebuild()`?
5. Как request_id попадает в логи и в ответ?

<details>
<summary>Ключи</summary>

- TODO

</details>

---

## Шаг 2 — Persistence

1. Что такое `UnitOfWork` в этом проекте: объект с логикой или «сумка репозиториев»?
2. Кто вызывает `commit()` — service или deps/scope?
3. Зачем `uow.py` и `uow_factory.py` разделены?
4. Возьми `BookingStatus` — перечисли статусы из кода (не по памяти).
5. Как Alembic узнаёт о моделях для autogenerate?

<details>
<summary>Ключи</summary>

- TODO

</details>

---

## Шаг 3 — Contracts

1. Почему request и response schema разделены?
2. Какой envelope у списков (pagination)?
3. Что такое Problem JSON в этом проекте (поля)?
4. Где живёт общий base repository / pagination helper?
5. Можно ли отдавать ORM-модель напрямую из router? Почему?

<details>
<summary>Ключи</summary>

- TODO

</details>

---

## Шаг 4 — Auth + Identity

1. Где хранится refresh token (cookie vs body) и почему это важно?
2. Чем `identity` отличается от `auth` по ответственности?
3. Как проверяется членство в студии (модель + policy/dependency)?
4. Что происходит с soft-deleted user при попытке логина?
5. Какие публичные функции auth экспортирует для других модулей?

<details>
<summary>Ключи</summary>

- TODO

</details>

---

## Шаг 5 — Catalog

1. Связь Studio → Service → Occurrence: какие FK?
2. Зачем `ScheduleTemplate` и кто генерирует occurrences?
3. Чем `catalog/public` отличается от owner routers?
4. Какие статусы/visibility есть у Service / Occurrence?
5. Почему catalog не должен знать про payment?

<details>
<summary>Ключи</summary>

- TODO

</details>

---

## Шаг 6 — Booking

1. Что такое pending hold и где TTL/expire логика?
2. Как обеспечивается capacity / уникальность активного бронирования?
3. Роль `Order` относительно `Booking`.
4. Что делает lifecycle job каждые 5 минут?
5. Где лежат policies вроде `is_own_booking` и кто их вызывает?

<details>
<summary>Ключи</summary>

- TODO

</details>

---

## Шаг 7 — Payment

1. Последовательность: create checkout → webhook → confirm seats.
2. Зачем `ProcessedWebhookEvent`?
3. Что такое ledger / `manual_review` в этом коде?
4. Где граница `integrations/stripe` vs `modules/payment`?
5. Что блокирует оплату, если Connect не готов?

<details>
<summary>Ключи</summary>

- TODO

</details>

---

## Шаг 8 — Search + Ops

1. Search — отдельный write-домен или read-only leaf?
2. Какие cron/scripts есть и идемпотентны ли они?
3. Где rate limiting и что будет без Redis в multi-instance?
4. Какие метрики/health отдаёт API?
5. Как локально прогнать booking-lifecycle?

<details>
<summary>Ключи</summary>

- TODO

</details>

---

## Шаг 9 — Synthesis

1. Нарисуй sequence: guest создаёт booking и платит (модули + ключевые функции).
2. Что случится, если webhook пришёл дважды?
3. Что случится, если hold истёк, а оплата пришла позже?
4. Куда положить новый endpoint «список моих заказов» и какие слои создать?
5. Какой тест/линтер упадёт, если `catalog` импортирует `payment.service`?

<details>
<summary>Ключи</summary>

- TODO

</details>
