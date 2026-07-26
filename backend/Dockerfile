FROM python:3.13-slim

WORKDIR /app

# Install dependencies in a separate layer (cached when lockfile unchanged).
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

# Copy application code
COPY . .

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
