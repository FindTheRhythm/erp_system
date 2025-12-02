FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Запускаем миграции и затем сервер
CMD sh -c "cd /app && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"

