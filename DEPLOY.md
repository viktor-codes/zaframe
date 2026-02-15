# ZaFrame — деплой MVP для презентации

## Быстрый старт: только лендинг (без бэкенда)

Подходит для демо главной страницы: Hero, Manifesto, How it works, поиск, Moments.

### 1. Фронтенд на Vercel

- **Корень проекта для Vercel:** папка `frontend` (в настройках проекта → Root Directory: `frontend`).
- Переменные окружения для «только лендинг»: **не задавать** `NEXT_PUBLIC_API_URL`.
- В этом режиме маршруты `/studios`, `/dashboard`, `/bookings`, `/auth` редиректятся на главную.

**Деплой через Vercel Dashboard:**

1. [vercel.com](https://vercel.com) → New Project → Import Git (GitHub/GitLab).
2. **Root Directory:** `frontend` → Edit → `frontend` → Save.
3. **Build Command:** `npm run build` (уже в `vercel.json`).
4. **Environment Variables:** не добавлять `NEXT_PUBLIC_API_URL` для режима лендинга.
5. Deploy.

**Деплой через CLI (из репозитория):**

```bash
cd frontend && vercel
# При первом запуске: выбери scope, создай проект, Root Directory оставь . (текущая папка)
```

---

## Полный MVP: фронт + API + БД

Чтобы работали студии, поиск, брони и (опционально) оплата. Порядок: **БД → бэкенд → миграции и сид → переменная на Vercel**.

---

### Шаг 1. База данных (PostgreSQL)

Нужна PostgreSQL. Рекомендуем **Neon** (бесплатный тир, быстрый старт).

1. [neon.tech](https://neon.tech) → **Create Project** → выбери регион.
2. В проекте: **Connection string** → скопируй строку (PostgreSQL).
3. Для SQLAlchemy async замени протокол на `postgresql+asyncpg://` и при необходимости добавь `?sslmode=require`.

   Пример: `postgresql+asyncpg://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require`

---

### Шаг 2. Деплой бэкенда (Railway или Render)

#### Вариант A: Railway

1. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub** → выбери репо `zaframe`.
2. **Settings** проекта → **Root Directory**: `backend`.
3. Добавь сервис **PostgreSQL** (или используй внешнюю БД из шага 1).
4. В сервисе приложения (не БД) → **Variables** добавь:

   | Переменная      | Значение |
   |-----------------|----------|
   | `DATABASE_URL`  | Строка из Neon (формат `postgresql+asyncpg://...`) |
   | `SECRET_KEY`    | `openssl rand -hex 32` (выполни в терминале) |
   | `FRONTEND_URL`  | URL твоего фронта на Vercel, например `https://zaframe.vercel.app` |
   | `CORS_ORIGINS`  | То же значение, что и `FRONTEND_URL` |

5. **Settings** → **Deploy** → **Start Command** (если не подхватилось):  
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`  
   (Railway подставляет `PORT` сам.)
6. Деплой → скопируй **URL сервиса** (например `https://zaframe-api.up.railway.app`).

#### Вариант B: Render

1. [render.com](https://render.com) → **New** → **Web Service** → подключи репо `zaframe`.
2. **Root Directory:** `backend`.
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Environment** — добавь те же переменные, что в таблице выше (`DATABASE_URL`, `SECRET_KEY`, `FRONTEND_URL`, `CORS_ORIGINS`).
6. **Create Web Service** → дождись деплоя → скопируй URL (например `https://zaframe-api.onrender.com`).

Либо используй **Blueprint**: в корне репо есть `render.yaml` — **New → Blueprint** и укажи этот репо.

---

### Шаг 3. Миграции и тестовые данные

После первого деплоя бэкенда нужно применить миграции и (по желанию) заполнить БД студиями.

**Локально** (с продовой БД):

```bash
cd backend
# В .env пропиши DATABASE_URL от Neon (или от Railway PostgreSQL)
uv sync
uv run alembic upgrade head
uv run python -m app.seed
```

Либо на Railway/Render можно один раз выполнить команды через **one-off job** (если платформа поддерживает), либо временно подставить `DATABASE_URL` в локальный `.env` и выполнить команды выше.

---

### Шаг 4. Подключить фронт к API (Vercel)

1. Vercel → твой проект (фронт) → **Settings** → **Environment Variables**.
2. Добавь переменную:
   - **Name:** `NEXT_PUBLIC_API_URL`
   - **Value:** URL бэкенда **без слэша в конце** (например `https://zaframe-api.onrender.com` или `https://zaframe-api.up.railway.app`).
3. **Save** → сделай **Redeploy** проекта (Deployments → ⋮ → Redeploy).

После редеплоя фронт будет слать запросы на твой API: поиск, список студий и карточка студии заработают.

---

## Чеклист: подключить всё

- [ ] **БД:** создан проект в Neon, скопирован `DATABASE_URL` в формате `postgresql+asyncpg://...`.
- [ ] **Бэкенд:** задеплоен на Railway или Render (Root Directory: `backend`), заданы `DATABASE_URL`, `SECRET_KEY`, `FRONTEND_URL`, `CORS_ORIGINS`.
- [ ] **Миграции и сид:** выполнены `alembic upgrade head` и `python -m app.seed` (локально с продовой БД или через one-off job).
- [ ] **Фронт:** в Vercel в Environment Variables добавлен `NEXT_PUBLIC_API_URL` = URL бэкенда (без слэша), сделан Redeploy.
- [ ] **Проверка:** открыл продовый фронт → поиск → переход в список студий → карточка студии.

---

## Полезные команды

```bash
# Фронт: сборка
cd frontend && npm run build

# Бэкенд локально (нужен .env с DATABASE_URL и др.)
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Миграции (при изменении моделей)
cd backend && uv run alembic upgrade head

# Сид — тестовые студии для презентации
cd backend && uv run python -m app.seed

# Сгенерировать SECRET_KEY
openssl rand -hex 32
```
