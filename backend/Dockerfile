FROM python:3.12-slim

WORKDIR /app

# Устанавливаем зависимости отдельным слоем (кэшируется)
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

# Копируем код
COPY . .

# Запускаем
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]