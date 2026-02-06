"""
Точка входа приложения ZaFrame API.

main.py остаётся минимальным: создание app, подключение роутеров, lifespan (позже).
Вся логика — в модулях core/, api/, services/.
"""
from fastapi import FastAPI

from app.api.v1 import health

app = FastAPI(title="ZaFrame API")

# Один роутер — два префикса: без дублирования кода.
# 1) Корень: / и /health — для load balancer'ов, k8s probes, мониторинга.
# 2) Версионированный API: /api/v1/ и /api/v1/health — для клиентов.
app.include_router(health.router)
app.include_router(health.router, prefix="/api/v1")