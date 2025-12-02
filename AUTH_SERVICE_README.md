# Auth Service - Документация

## Реализованный функционал

### Backend (Auth Service)

1. **Простая авторизация без БД**
   - Хардкод пользователей: `admin/admin` и `viewer/viewer`
   - Валидация: минимум 5 символов, только латиница
   - Роли: `admin` и `viewer`

2. **Endpoints**
   - `POST /auth/login` - вход пользователя
   - `POST /auth/logout` - выход пользователя

3. **RabbitMQ события**
   - `user.login` - при успешном входе
   - `user.logout` - при выходе

4. **Структура файлов**
   ```
   backend/auth_service/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py          # FastAPI приложение
   │   ├── config.py        # Настройки
   │   ├── models.py        # Pydantic модели
   │   ├── auth_service.py  # Бизнес-логика
   │   ├── rabbitmq_client.py  # RabbitMQ клиент
   │   └── routers/
   │       ├── __init__.py
   │       └── auth.py      # Роутеры авторизации
   ├── Dockerfile
   └── requirements.txt
   ```

### Frontend

1. **Страница авторизации** (`/login`)
   - Поля: логин и пароль
   - Валидация на клиенте
   - Показ ошибок

2. **Защита маршрутов**
   - Автоматический редирект на `/login` если не авторизован
   - Защита главной страницы (`/`)

3. **Хранение сессии**
   - localStorage для сохранения пользователя
   - Автоматическое восстановление сессии при перезагрузке

4. **Структура файлов**
   ```
   frontend/src/
   ├── api/
   │   └── auth.ts          # API клиент для Auth Service
   ├── context/
   │   └── AuthContext.tsx   # Контекст авторизации
   ├── pages/
   │   ├── Login.tsx        # Страница входа
   │   └── Dashboard.tsx    # Главная страница
   ├── components/
   │   └── ProtectedRoute.tsx  # Защита маршрутов
   └── App.tsx              # Роутинг
   ```

### API Gateway

- Проксирование запросов к Auth Service
- Маршрут: `/auth/*` → `http://auth_service:8000/auth/*`

## Тестовые пользователи

- **Администратор**: `admin` / `admin`
- **Просмотр**: `viewer` / `viewer`

## API Endpoints

### POST /auth/login
**Request:**
```json
{
  "username": "admin",
  "password": "admin"
}
```

**Response (успех):**
```json
{
  "success": true,
  "message": "Успешный вход",
  "role": "admin"
}
```

**Response (ошибка):**
```json
{
  "success": false,
  "message": "Неверный логин или пароль",
  "role": null
}
```

### POST /auth/logout
**Request:**
```json
{
  "username": "admin",
  "role": "admin"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Успешный выход"
}
```

## RabbitMQ события

### user.login
Отправляется при успешном входе:
```json
{
  "username": "admin",
  "role": "admin"
}
```

### user.logout
Отправляется при выходе:
```json
{
  "username": "admin",
  "role": "admin"
}
```

## Проверка работы

1. Запустить все сервисы:
   ```bash
   docker-compose up -d
   ```

2. Открыть http://localhost:3000
   - Должен быть редирект на `/login`

3. Войти как `admin` / `admin`
   - Должен быть редирект на главную страницу
   - В шапке должно отображаться: `admin (admin)`

4. Проверить RabbitMQ Management (http://localhost:15672)
   - Exchange `erp_events` должен быть создан
   - События `user.login` и `user.logout` должны отправляться

5. Проверить API напрямую:
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin"}'
   ```

## Следующие шаги

- [ ] Добавить больше страниц для разных ролей
- [ ] Реализовать разграничение прав доступа по ролям
- [ ] Добавить обработку событий в Notifications Service

