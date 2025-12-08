# Архитектура фронтенда ERP System

Документ описывает архитектуру, структуру кода, взаимодействие с бекендом и процесс сборки/развертывания фронтенда.

---

## 1. Расположение основного кода архитектуры фронтенда

### Структура проекта

```
frontend/
├── src/
│   ├── App.tsx                    # Главный компонент приложения (роутинг)
│   ├── index.tsx                 # Точка входа приложения
│   ├── index.css                 # Глобальные стили
│   │
│   ├── api/                      # API клиенты для взаимодействия с бекендом
│   │   ├── auth.ts               # API для аутентификации
│   │   ├── catalog.ts            # API для каталога товаров
│   │   ├── inventory.ts          # API для остатков
│   │   └── warehouse.ts          # API для склада
│   │
│   ├── components/               # Переиспользуемые компоненты
│   │   ├── Layout.tsx           # Основной layout с навигацией
│   │   ├── ProtectedRoute.tsx   # Компонент защиты маршрутов
│   │   ├── CircularProgressChart.tsx
│   │   └── LocationItemsList.tsx
│   │
│   ├── context/                  # React Context для глобального состояния
│   │   └── AuthContext.tsx       # Контекст аутентификации
│   │
│   ├── pages/                    # Страницы приложения
│   │   ├── Login.tsx            # Страница входа
│   │   ├── Dashboard.tsx        # Главная страница
│   │   ├── CatalogList.tsx      # Список товаров
│   │   ├── CatalogForm.tsx      # Форма создания/редактирования товара
│   │   ├── CatalogDetail.tsx    # Детали товара
│   │   ├── InventoryList.tsx    # Список остатков
│   │   ├── OperationsList.tsx   # Список операций
│   │   └── WarehousePage.tsx     # Страница склада
│   │
│   └── utils/                    # Утилиты
│       └── errorHandler.ts       # Обработка ошибок API
│
├── public/
│   └── index.html                # HTML шаблон
│
├── package.json                  # Зависимости и скрипты
├── tsconfig.json                 # Конфигурация TypeScript
└── Dockerfile                    # Docker конфигурация для разработки
```

### Основные файлы архитектуры:

#### 1. **`src/App.tsx`** - Главный компонент приложения
- Определяет маршрутизацию приложения (React Router)
- Оборачивает приложение в `AuthProvider` для глобального управления аутентификацией
- Защищает маршруты через `ProtectedRoute`
- **Маршруты:**
  - `/login` - страница входа
  - `/` - Dashboard (главная)
  - `/catalog` - список товаров
  - `/catalog/new` - создание товара
  - `/catalog/:id` - детали товара
  - `/catalog/:id/edit` - редактирование товара
  - `/inventory` - остатки
  - `/inventory/operations` - операции
  - `/warehouse` - склад

#### 2. **`src/index.tsx`** - Точка входа
- Инициализирует React приложение
- Рендерит корневой компонент `App`
- Подключает глобальные стили

#### 3. **`src/context/AuthContext.tsx`** - Контекст аутентификации
- Управляет состоянием пользователя (авторизован/не авторизован)
- Хранит информацию о пользователе (username, role)
- Предоставляет методы `login()` и `logout()`
- Сохраняет сессию в `localStorage`
- Восстанавливает сессию при перезагрузке страницы

#### 4. **`src/components/Layout.tsx`** - Основной layout
- Содержит AppBar с информацией о пользователе
- Боковое меню (Drawer) с навигацией
- Оборачивает содержимое страниц

#### 5. **`src/components/ProtectedRoute.tsx`** - Защита маршрутов
- Проверяет аутентификацию пользователя
- Перенаправляет на `/login` если не авторизован
- Отображает Layout для авторизованных пользователей

---

## 2. Библиотека для общения с API Gateway и коды операций

### Библиотека: **Axios** (`axios` версия 1.6.2)

Axios используется для всех HTTP запросов к API Gateway.

**Установка:** Уже включена в `package.json`:
```json
"axios": "^1.6.2"
```

### Расположение кодов операций связи фронтенда и бекенда:

Все API клиенты находятся в директории **`frontend/src/api/`**:

#### **`frontend/src/api/auth.ts`** - Аутентификация
```typescript
// Базовый URL API Gateway
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Создание axios instance для auth
const authApi = axios.create({
  baseURL: `${API_URL}/auth`,
  headers: { 'Content-Type': 'application/json' }
});

// Методы:
- authService.login(username, password)      // POST /auth/login
- authService.logout(username, role)         // POST /auth/logout
```

#### **`frontend/src/api/catalog.ts`** - Каталог товаров
```typescript
const catalogApi = axios.create({
  baseURL: `${API_URL}/catalog`,
  headers: { 'Content-Type': 'application/json' }
});

// Interceptor для добавления заголовка с ролью пользователя
catalogApi.interceptors.request.use((config) => {
  const headers = getHeaders(); // Получает роль из localStorage
  Object.assign(config.headers, headers);
  return config;
});

// Методы:
- catalogService.getUnits(type?)                    // GET /catalog/units
- catalogService.createUnit(unit)                   // POST /catalog/units
- catalogService.getSKUs(params?)                   // GET /catalog/skus
- catalogService.getSKU(id)                        // GET /catalog/skus/:id
- catalogService.searchSKUs(q, limit?)             // GET /catalog/skus/search
- catalogService.createSKU(sku)                    // POST /catalog/skus
- catalogService.updateSKU(id, sku)                // PUT /catalog/skus/:id
- catalogService.deleteSKU(id)                     // DELETE /catalog/skus/:id
- catalogService.exportCSV()                        // GET /catalog/skus/export/csv
- catalogService.importCSV(file)                   // POST /catalog/skus/import/csv
```

#### **`frontend/src/api/inventory.ts`** - Остатки
```typescript
const inventoryApi = axios.create({
  baseURL: `${API_URL}/inventory`,
  headers: { 'Content-Type': 'application/json' }
});

// Методы:
- inventoryService.getOperations(params?)          // GET /inventory/operations
- inventoryService.createOperation(operation)      // POST /inventory/operations
- inventoryService.getSKUHistory(skuId, params?)    // GET /inventory/sku/:id/history
- inventoryService.getSKUTotals(params?)           // GET /inventory/sku/totals
- inventoryService.getLocationTotals(params?)       // GET /inventory/locations
- inventoryService.getLocationTotalsByLocation(name) // GET /inventory/locations/:name
```

#### **`frontend/src/api/warehouse.ts`** - Склад
```typescript
const warehouseApi = axios.create({
  baseURL: `${API_URL}/warehouse`,
  headers: { 'Content-Type': 'application/json' }
});

// Interceptor для добавления заголовка с ролью пользователя
warehouseApi.interceptors.request.use((config) => {
  const headers = getHeaders();
  Object.assign(config.headers, headers);
  return config;
});

// Методы:
- warehouseService.getLocations()                  // GET /warehouse/locations
- warehouseService.getLocation(locationId)          // GET /warehouse/locations/:id
- warehouseService.getLocationsStats()             // GET /warehouse/locations/stats
- warehouseService.getOperations()                 // GET /warehouse/operations
- warehouseService.getOperation(operationId)       // GET /warehouse/operations/:id
- warehouseService.createOperation(operation)     // POST /warehouse/operations
- warehouseService.getTempStorageItems()           // GET /warehouse/temp-storage
- warehouseService.processTempStorage()            // POST /warehouse/temp-storage/process
```

### Передача роли пользователя:

Для сервисов `catalog` и `warehouse` используется заголовок `X-User-Role`, который автоматически добавляется через axios interceptor:

```typescript
const getHeaders = (): { 'X-User-Role': string } => {
  const userStr = localStorage.getItem('user');
  if (userStr) {
    const user = JSON.parse(userStr);
    return { 'X-User-Role': user.role || 'viewer' };
  }
  return { 'X-User-Role': 'viewer' };
};
```

---

## 3. Код отправки запросов между фронтендом и бекендом

### Где найти код отправки запросов:

#### **1. API клиенты** (`frontend/src/api/*.ts`)
Все запросы определены в файлах API клиентов (см. раздел 2).

#### **2. Использование в компонентах**

**Пример из `src/pages/Login.tsx`:**
```typescript
import { authService } from '../api/auth';

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  try {
    await login(username, password); // Вызывает authService.login()
    navigate('/');
  } catch (err: any) {
    setError(err.message || 'Ошибка входа');
  }
};
```

**Пример из `src/context/AuthContext.tsx`:**
```typescript
import { authService, LoginResponse } from '../api/auth';

const login = async (username: string, password: string): Promise<void> => {
  try {
    const response: LoginResponse = await authService.login(username, password);
    // Обработка ответа...
  } catch (error: any) {
    // Обработка ошибок...
  }
};
```

#### **3. Обработка ошибок**

**`frontend/src/utils/errorHandler.ts`** - утилита для форматирования ошибок:
```typescript
export const formatApiError = (error: any): string => {
  // Обрабатывает различные форматы ошибок от FastAPI/Pydantic
  // - Строки
  // - Объекты с detail
  // - Массивы ошибок валидации
  // - Сообщения об ошибках
}
```

### Поток запроса:

1. **Компонент** вызывает метод из API сервиса (например, `catalogService.getSKUs()`)
2. **API клиент** (`catalog.ts`) создает HTTP запрос через axios
3. **Axios interceptor** добавляет заголовки (например, `X-User-Role`)
4. **Запрос отправляется** на API Gateway (`http://localhost:8000/catalog/skus`)
5. **API Gateway** проксирует запрос к соответствующему микросервису
6. **Ответ возвращается** через API Gateway обратно в компонент
7. **Компонент обрабатывает** данные или ошибки

### Конфигурация API URL:

API URL настраивается через переменную окружения:
```typescript
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

В `docker-compose.yml`:
```yaml
frontend:
  environment:
    - REACT_APP_API_URL=http://localhost:8000
```

---

## 4. Сборка, оптимизация и развертывание (Dockerfiles)

### Текущий Dockerfile (для разработки):

**`frontend/Dockerfile`**:
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
```

**Особенности:**
- Использует `node:18-alpine` (легковесный образ)
- Устанавливает зависимости через `npm install`
- Запускает dev-сервер через `npm start` (react-scripts)
- **Не оптимизирован для production** - это Dockerfile для разработки

### Процесс сборки:

#### **Development сборка:**
```bash
npm start
# Запускает dev-сервер на http://localhost:3000
# Hot reload включен
# Source maps включены
```

#### **Production сборка:**
```bash
npm run build
# Создает оптимизированную сборку в папке build/
# Минификация кода
# Оптимизация изображений
# Tree shaking (удаление неиспользуемого кода)
# Code splitting
```

### Оптимизации в production сборке (react-scripts):

React Scripts автоматически применяет следующие оптимизации:

1. **Минификация JavaScript и CSS**
2. **Tree shaking** - удаление неиспользуемого кода
3. **Code splitting** - разделение кода на chunks
4. **Оптимизация изображений**
5. **Gzip compression** (если настроен веб-сервер)
6. **Source maps** (опционально, для отладки)

### Рекомендуемый Production Dockerfile:

Для production рекомендуется использовать multi-stage build:

```dockerfile
# Stage 1: Build
FROM node:18-alpine AS builder

WORKDIR /app

# Копируем package файлы
COPY package*.json ./

# Устанавливаем зависимости
RUN npm ci --only=production

# Копируем исходный код
COPY . .

# Собираем приложение
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Копируем собранное приложение из builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Копируем конфигурацию nginx (опционально)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**Преимущества production Dockerfile:**
- ✅ Меньший размер образа (только nginx + статические файлы)
- ✅ Быстрый запуск (нет Node.js)
- ✅ Оптимизированная производительность (nginx для статики)
- ✅ Безопасность (меньше зависимостей)

### Конфигурация nginx для SPA (опционально):

**`nginx.conf`**:
```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;

    # SPA routing - все запросы на index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Кэширование статических файлов
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Переменные окружения:

Для production сборки переменные окружения должны быть заданы на этапе сборки:

```dockerfile
# В Dockerfile для production
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# При сборке:
docker build --build-arg REACT_APP_API_URL=https://api.example.com -t erp-frontend .
```

### Развертывание через Docker Compose:

**Текущая конфигурация** (`docker-compose.yml`):
```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  container_name: erp_frontend
  environment:
    - REACT_APP_API_URL=http://localhost:8000
  ports:
    - "3000:3000"
  depends_on:
    - api_gateway
  networks:
    - erp_network
```

**Для production рекомендуется:**
1. Использовать production Dockerfile с nginx
2. Настроить правильный `REACT_APP_API_URL`
3. Использовать reverse proxy (nginx/traefik) для SSL
4. Настроить кэширование статических файлов

### Скрипты сборки:

**`package.json`**:
```json
{
  "scripts": {
    "start": "react-scripts start",        // Dev сервер
    "build": "react-scripts build",        // Production сборка
    "test": "react-scripts test",          // Тесты
    "eject": "react-scripts eject"         // Извлечение конфигурации (не рекомендуется)
  }
}
```

### Браузерная поддержка:

**`package.json`** (browserslist):
```json
{
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
```

---

## Резюме

### Архитектура:
- ✅ **React 18** с TypeScript
- ✅ **React Router** для маршрутизации
- ✅ **Material-UI** для UI компонентов
- ✅ **Context API** для глобального состояния
- ✅ **Axios** для HTTP запросов

### API взаимодействие:
- ✅ Все запросы идут через **API Gateway** (`http://localhost:8000`)
- ✅ API клиенты в `frontend/src/api/`
- ✅ Автоматическая передача роли через заголовок `X-User-Role`

### Сборка:
- ⚠️ Текущий Dockerfile - для **разработки** (dev-сервер)
- ✅ Production сборка через `npm run build`
- ✅ Рекомендуется использовать **multi-stage build** с nginx для production

### Оптимизации:
- ✅ Автоматические оптимизации через react-scripts
- ✅ Минификация, tree shaking, code splitting
- ✅ Рекомендуется настроить nginx для статических файлов


