# ERP System - Система управления складскими запасами и логистикой

Микросервисная архитектура для управления складскими запасами и логистикой для малого бизнеса.

## Архитектура

Система построена на микросервисной архитектуре с использованием:
- **Backend**: Python + FastAPI
- **Frontend**: React + TypeScript + Material-UI
- **Database**: PostgreSQL
- **Message Broker**: RabbitMQ
- **Containerization**: Docker

## Структура проекта

```
erp_system/
├── backend/              # Все микросервисы
│   ├── api_gateway/      # API Gateway / BFF
│   ├── auth_service/     # Сервис аутентификации
│   ├── catalog_service/  # Сервис каталога товаров (SKU)
│   ├── inventory_service/ # Сервис управления остатками
│   ├── warehouse_service/ # Сервис управления складом
│   ├── orders_service/   # Сервис управления заказами
│   └── notifications_service/ # Сервис уведомлений
├── frontend/             # React приложение
├── docker-compose.yml    # Конфигурация Docker Compose
├── .env                  # Переменные окружения (создать из env.example)
└── env.example           # Пример переменных окружения
```

**Важно:** Файл `.env` должен находиться в **корне проекта** (рядом с `docker-compose.yml`). Docker Compose автоматически читает переменные из этого файла.

## Микросервисы

### 1. Auth Service (Порт: 8001)
- Регистрация и аутентификация пользователей
- JWT токены (access/refresh)
- Управление ролями

### 2. Catalog Service (Порт: 8002)
- CRUD операций для SKU (товаров)
- Управление атрибутами товаров
- Импорт/экспорт CSV

### 3. Inventory Service (Порт: 8003)
- Управление остатками по локациям
- Операции: приём, списание, перемещение
- Корректировки остатков
- Отчёты по движению товара

### 4. Warehouse Service (Порт: 8004)
- Управление локациями (склады/зоны/ячейки)
- Приёмка поставок (PO → Receipt)
- Pick & Pack задачи
- Внутренние перемещения

### 5. Orders Service (Порт: 8005)
- Создание и управление заказами
- Резервирование товаров
- Статусы заказов (created, reserved, picking, picked, shipped, cancelled)

### 6. Notifications Service (Порт: 8006)
- Обработка событий из RabbitMQ
- Логирование операций
- Уведомления о событиях

### 7. API Gateway (Порт: 8000)
- Единая точка входа для всех запросов
- Маршрутизация к микросервисам
- Аутентификация и авторизация

### 8. Frontend (Порт: 3000)
- React + TypeScript + Material-UI
- Веб-интерфейс для всех операций

## Запуск проекта

### Требования
- Docker и Docker Compose
- Git

### Установка и запуск

1. Клонируйте репозиторий (если нужно)
2. **Создайте файл `.env` в корне проекта** (рядом с `docker-compose.yml`):
   ```bash
   # Windows
   copy env.example .env
   
   # Linux/Mac
   cp env.example .env
   ```
3. При необходимости отредактируйте `.env` и настройте переменные окружения
4. Запустите все сервисы:
   ```bash
   docker-compose up -d
   ```
5. Проверьте статус:
   ```bash
   docker-compose ps
   ```

### Доступ к сервисам

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **RabbitMQ Management**: http://localhost:15672 (rabbitmq/rabbitmq_password)
- **PostgreSQL**: localhost:5432

### Остановка

```bash
docker-compose down
```

Для удаления данных:
```bash
docker-compose down -v
```

## Разработка

Каждый микросервис находится в `backend/` и имеет:
- `Dockerfile` - для контейнеризации
- `requirements.txt` - зависимости Python
- `app/` - основной код приложения

**Переменные окружения:**
- Файл `.env` должен находиться в **корне проекта** (рядом с `docker-compose.yml`)
- Все сервисы читают переменные из этого файла через Docker Compose
- Файл `.env` не должен попадать в git (уже добавлен в `.gitignore`)

## Технологии

- **Python 3.11+**
- **FastAPI**
- **PostgreSQL 15**
- **RabbitMQ 3**
- **React 18+**
- **TypeScript**
- **Material-UI (MUI)**
- **Docker & Docker Compose**

## Статус разработки

Проект в стадии разработки. Структура создана, микросервисы будут реализовываться поэтапно.

