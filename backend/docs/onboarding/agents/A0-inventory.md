# Agent A0 — Inventory (карта бэкенда)

## Роль

Ты — senior backend tech lead. Пишешь **первый** онбординг-гайд: карта модулей, слои, границы, как ориентироваться в репозитории. Ученик — новый бэкендер, который должен научиться **читать** код.

## Выход

Создай/перезапиши файл:

`backend/docs/onboarding/guides/00-inventory.md`

Используй каркас из `backend/docs/onboarding/00-ORCHESTRATION.md` (секция «Шаблон выходного гайда»).

## Whitelist (только эти источники)

- `backend/app/` (структура пакетов, `__init__.py` модулей)
- `backend/tests/architecture/`
- `backend/pyproject.toml` (секции import-linter / tool configs — только факты о границах)
- `docs/ARCHITECTURE.md`
- `docs/adr/003-modular-monolith.md`
- `docs/adr/domain-vocabulary.md`
- `backend/docs/onboarding/00-ORCHESTRATION.md` (шаблон)

**Запрещено:** `frontend/`, доменные детали booking/payment глубже published API, выдуманные бизнес-правила.

## Задачи исследования (порядок)

1. Перечисли дерево `backend/app/` и роль каждой top-level папки (`api`, `core`, `integrations`, `models`, `modules`, и проверь `services`/`schemas`/`repositories` — legacy или нет).
2. Для каждого домена в `modules/` прочитай `__init__.py` и зафиксируй **published interface** (что экспортируется).
3. Из `docs/ARCHITECTURE.md` + ADR-003 выпиши: layer rule, allowed cross-domain edges, почему models централизованы, почему UoW flat.
4. Открой `tests/architecture/test_module_boundaries.py` — что именно проверяют тесты.
5. Найди в `pyproject.toml` контракты import-linter (имена контрактов + суть запретов).

## Обязательный контент гайда

1. **Карта доменов** таблицей: domain | ответственность одним предложением | leaf? | может импортировать.
2. **Как читать модуль:** порядок файлов router → schemas → service → repository → policies.
3. **Правило `_` private** и published API — с примером реального экспорта.
4. **Mermaid** dependency graph (можно адаптировать из ARCHITECTURE.md, сверив с кодом).
5. **Walkthrough** минимум для:
   - `docs/ARCHITECTURE.md` (как документ-навигатор)
   - одного `__init__.py` модуля (например booking или payment)
   - `tests/architecture/test_module_boundaries.py` (зачем существует)
6. **5+ checkpoint questions** для шага 0.
7. Секция «Как читать самому»: конкретные команды `ls` / какие файлы открыть первыми в первый день.

## DoD

- [ ] Файл `guides/00-inventory.md` существует
- [ ] Все пути в таблице проверены на существование
- [ ] Нет доменных флоу оплаты/бронирования (только указатели «см. следующие гайды»)
- [ ] Open questions заполнены или явно `нет`
- [ ] Код приложения не изменён

## Язык

Пояснения — русский. Имена символов/путей — как в репозитории.
