# Быстрый старт

## Первый запуск

1. **Создайте файл `.env` в корне проекта** (рядом с `docker-compose.yml`):
   ```bash
   # Windows
   copy env.example .env
   
   # Linux/Mac
   cp env.example .env
   ```
   **Важно:** Файл `.env` должен находиться в корне проекта, рядом с `docker-compose.yml`

2. **Запустите все сервисы:**
   ```bash
   docker-compose up -d
   ```

3. **Проверьте статус сервисов:**
   ```bash
   docker-compose ps
   ```

4. **Проверьте логи (если нужно):**
   ```bash
   docker-compose logs -f
   ```

## Проверка работоспособности

После запуска проверьте доступность сервисов:

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **Auth Service**: http://localhost:8001/health
- **Catalog Service**: http://localhost:8002/health
- **Inventory Service**: http://localhost:8003/health
- **Warehouse Service**: http://localhost:8004/health
- **Orders Service**: http://localhost:8005/health
- **Notifications Service**: http://localhost:8006/health
- **RabbitMQ Management**: http://localhost:15672 (логин: rabbitmq, пароль: rabbitmq_password)
- **PostgreSQL**: localhost:5432

## Остановка

```bash
docker-compose down
```

Для полной очистки (включая volumes):
```bash
docker-compose down -v
```

## Пересборка после изменений

Если вы изменили код, пересоберите образы:
```bash
docker-compose build
docker-compose up -d
```

Или для конкретного сервиса:
```bash
docker-compose build auth_service
docker-compose up -d auth_service
```

