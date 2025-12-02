# Отладка проблемы с редиректом на /login

## Проблема
При переходе на localhost:3000 не происходит редирект на /login

## Возможные причины

1. **В localStorage есть старые данные пользователя**
   - Решение: Очистить localStorage в браузере
   - В консоли браузера: `localStorage.removeItem('user')`

2. **isLoading остается true**
   - Проверить консоль браузера на наличие ошибок
   - Проверить логику в AuthContext

3. **Проблема с роутингом**
   - Проверить что React Router работает
   - Проверить что ProtectedRoute вызывается

## Шаги для отладки

1. Откройте консоль браузера (F12)
2. Перейдите на localhost:3000
3. Проверьте логи:
   - `AuthContext: Checking saved user: ...`
   - `ProtectedRoute: isLoading= ... isAuthenticated= ...`
4. Если в localStorage есть данные - очистите их:
   ```javascript
   localStorage.removeItem('user')
   ```
5. Обновите страницу

## Проверка API Gateway

Проверьте что API Gateway правильно проксирует запросы:
- Откройте Network tab в DevTools
- Попробуйте войти
- Проверьте запрос к `/auth/login`
- Должен быть статус 200, не 404


