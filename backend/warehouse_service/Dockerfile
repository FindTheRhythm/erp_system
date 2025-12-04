FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Делаем скрипт миграций исполняемым
RUN chmod +x run_migrations.sh || true

# Запускаем миграции, инициализацию данных и затем сервер
CMD sh -c "alembic stamp 001_initial 2>/dev/null || true; alembic upgrade head && python -m app.init_data && uvicorn app.main:app --host 0.0.0.0 --port 8000"

