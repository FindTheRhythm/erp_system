# Catalog Service - Frontend и Backend

## Что реализовано

### Backend (Catalog Service)

1. **Проверка ролей пользователя:**
   - Все endpoints для создания/редактирования/удаления требуют роль `admin`
   - Endpoints для просмотра доступны всем авторизованным пользователям
   - Роль передается через заголовок `X-User-Role` от API Gateway

2. **Endpoints с проверкой ролей:**
   - `POST /catalog/skus` - создание товара (admin only)
   - `PUT /catalog/skus/{id}` - обновление товара (admin only)
   - `DELETE /catalog/skus/{id}` - удаление товара (admin only)
   - `POST /catalog/units` - создание единицы измерения (admin only)
   - `POST /catalog/skus/import/csv` - импорт CSV (admin only)

3. **Endpoints доступные всем:**
   - `GET /catalog/skus` - список товаров
   - `GET /catalog/skus/{id}` - детали товара
   - `GET /catalog/skus/search` - поиск товаров
   - `GET /catalog/units` - список единиц измерения
   - `GET /catalog/skus/export/csv` - экспорт CSV

### Frontend

1. **Страницы:**
   - `/catalog` - список товаров (CatalogList)
   - `/catalog/new` - создание товара (CatalogForm)
   - `/catalog/:id` - детали товара (CatalogDetail)
   - `/catalog/:id/edit` - редактирование товара (CatalogForm)

2. **Компоненты:**
   - `Layout` - общий layout с навигацией и AppBar
   - `CatalogList` - список товаров с поиском, фильтрацией, экспортом/импортом CSV
   - `CatalogForm` - форма создания/редактирования товара
   - `CatalogDetail` - детальная информация о товаре

3. **Функциональность:**
   - Поиск товаров по названию или артикулу
   - Фильтрация по статусу
   - Создание/редактирование/удаление товаров (только для admin)
   - Экспорт/импорт CSV
   - Автоматическое добавление заголовка `X-User-Role` в запросы
   - Скрытие кнопок редактирования/удаления для пользователей с ролью `viewer`

## Как работает проверка ролей

1. **Frontend:**
   - При каждом запросе к Catalog API автоматически добавляется заголовок `X-User-Role` с ролью пользователя из localStorage
   - Кнопки создания/редактирования/удаления скрыты для пользователей с ролью `viewer`

2. **API Gateway:**
   - Передает заголовок `X-User-Role` от frontend к микросервисам
   - Если заголовок не передан, использует `viewer` по умолчанию

3. **Catalog Service:**
   - Читает роль из заголовка `X-User-Role`
   - Проверяет права доступа перед выполнением операций
   - Возвращает 403 ошибку если у пользователя нет прав
