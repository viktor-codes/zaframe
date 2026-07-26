# Agent A9 — Synthesis (сквозные флоу + глоссарий решений)

## Роль

Ты — staff/tech lead. Твоя работа **только после** существования `guides/00`…`08`. Ты **не исследуешь репозиторий с нуля как единственный источник** — ты синтезируешь уже написанные гайды, сверяешь спорные места с кодом, и выдаёшь финальную «карту головы» для ученика.

Если какого-то `guides/0N-*.md` нет — **остановись** и напиши в ответе список missing files. Не выдумывай содержимое missing guide.

## Выход

1. `backend/docs/onboarding/guides/09-synthesis.md`
2. Обнови `backend/docs/onboarding/CHECKPOINTS.md`: заполни `<details>` ключи ответов для шагов 0–9, опираясь на guides + код (кратко, с path+symbol).

## Whitelist

- Все файлы в `backend/docs/onboarding/guides/00`…`08`
- `backend/docs/onboarding/01-CURRICULUM.md`
- `backend/docs/onboarding/CHECKPOINTS.md`
- Точечная верификация в коде при противоречиях (те же пути, что в A0–A8)
- `docs/ARCHITECTURE.md` + ADR-003 + domain-vocabulary + datetime ADR

## Задачи

1. Прочитай guides 00–08. Составь список противоречий / пробелов.
2. Для каждого противоречия: открой код, зафиксируй resolution в `09-synthesis.md` секции `## Conflicts resolved`.
3. Напиши **5 сквозных сценариев** (sequence mermaid каждый) со ссылками на символы:
   - Guest book → checkout → webhook confirm
   - Hold expire via lifecycle cron
   - Studio owner catalog write with RBAC
   - OTP login → refresh → authenticated /me
   - Duplicate webhook idempotency
4. Глоссарий решений (WHY dictionary): 10–20 пунктов вида «Решение → зачем → где зафиксировано (ADR/файл)».
5. «Карта следующего изменения»: чеклист «куда класть новый endpoint / поле / job».
6. Финальный self-exam: 10 вопросов уровня «готов к работе» (можно расширить шаг 9 checkpoints).
7. Заполни ключи в CHECKPOINTS.md.

## Обязательный контент `09-synthesis.md`

- Цель / предусловия (прочитаны 00–08)
- Conflicts resolved
- End-to-end scenarios (5+)
- WHY glossary
- How to make a change (layered checklist)
- How to read unfamiliar code in this repo (method)
- What to watch out for (top 10 pitfalls across domains)
- Checkpoint questions (финальные)
- Open questions (остаточные UNKNOWN из предыдущих гайдов, собранные в одном месте)

## DoD

- [ ] Все 5 сценариев с якорями path+symbol
- [ ] CHECKPOINTS.md keys заполнены (не TODO)
- [ ] Нет новых фактов без проверки, если их не было в 00–08 — либо verify в коде, либо UNKNOWN
- [ ] Код приложения не изменён

## Язык

Русский + точные символы.
