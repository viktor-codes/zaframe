"""
Точка входа приложения ZaFrame API.

main.py остаётся минимальным: создание app, подключение роутеров, lifespan.
Вся логика — в модулях core/, api/, services/.
"""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, bookings, health, payments, services, slots, studios
from app.api.v1.endpoints import search
from app.api.webhooks import router as webhooks_router
from app.core.config import settings
from app.core.database import engine


# === Lifespan Context Manager ===
# Управляет жизненным циклом приложения: startup и shutdown события.
# Почему lifespan вместо @app.on_event:
# - Рекомендуемый способ в FastAPI (on_event deprecated)
# - Более явное управление ресурсами через context manager
# - Проще тестировать и мокировать
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager для управления подключением к БД.
    
    При старте: проверяем подключение к БД (опционально).
    При остановке: закрываем все соединения с БД.
    """
    # Startup: здесь можно добавить проверку подключения к БД
    # Пока просто пропускаем — engine сам управляет пулом соединений
    yield
    
    # Shutdown: закрываем все соединения с БД
    await engine.dispose()


# Используем настройки из config.py вместо хардкода.
# Теперь title и version централизованы и могут быть переопределены через .env
# lifespan=lifespan — подключаем управление жизненным циклом
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# === CORS Middleware ===
# Разрешаем запросы с фронтенда для разработки и production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Один роутер — два префикса: без дублирования кода.
# 1) Корень: / и /health — для load balancer'ов, k8s probes, мониторинга.
# 2) Версионированный API: /api/v1/ и /api/v1/health — для клиентов.
app.include_router(health.router)
app.include_router(health.router, prefix="/api/v1")
app.include_router(studios.router, prefix="/api/v1")
app.include_router(services.router, prefix="/api/v1")
app.include_router(slots.router, prefix="/api/v1")
app.include_router(bookings.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(webhooks_router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")