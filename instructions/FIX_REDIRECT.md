# Исправление проблемы с редиректом на /login

## Проблема
При переходе на localhost:3000 не происходит редирект на /login

## Причины

### 1. В localStorage есть старые данные пользователя
**Решение:**
- Откройте консоль браузера (F12)
- Выполните: `localStorage.removeItem('user')`
- Обновите страницу (F5)

### 2. Проблема с API Gateway (404 ошибка)
**Решение:**
- Перезапустите API Gateway: `docker-compose restart api_gateway`
- Проверьте логи: `docker-compose logs api_gateway`

### 3. Проверка логики редиректа
Откройте консоль браузера и проверьте логи:
- `AuthContext: Checking saved user: ...`
- `ProtectedRoute: isLoading= ... isAuthenticated= ...`

## Быстрое решение

1. **Очистить localStorage:**
   ```javascript
   localStorage.clear()
   ```
   Или только user:
   ```javascript
   localStorage.removeItem('user')
   ```

2. **Перезапустить сервисы:**
   ```bash
   docker-compose restart api_gateway frontend
   ```

3. **Проверить консоль браузера на наличие ошибок**

## Если проблема сохраняется

Проверьте в консоли браузера:
- Что показывает `localStorage.getItem('user')`?
- Что показывают логи `AuthContext` и `ProtectedRoute`?
- Есть ли ошибки в консоли?


