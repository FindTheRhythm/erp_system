/**
 * Утилита для обработки ошибок от API
 * FastAPI/Pydantic возвращает ошибки в разных форматах
 */
export const formatApiError = (error: any): string => {
  if (!error) {
    return 'Неизвестная ошибка';
  }

  // Если это строка, возвращаем как есть
  if (typeof error === 'string') {
    return error;
  }

  // Если есть response с данными
  if (error.response?.data) {
    const data = error.response.data;
    
    // Если есть detail
    if (data.detail) {
      const detail = data.detail;
      
      // Если detail - массив ошибок валидации
      if (Array.isArray(detail)) {
        return detail.map((e: any) => {
          if (typeof e === 'string') return e;
          // Форматируем ошибку валидации Pydantic
          if (e.msg) {
            const loc = Array.isArray(e.loc) ? e.loc.slice(1).join('.') : '';
            return loc ? `${loc}: ${e.msg}` : e.msg;
          }
          return JSON.stringify(e);
        }).join('; ');
      }
      
      // Если detail - строка
      if (typeof detail === 'string') {
        return detail;
      }
      
      // Если detail - объект
      return JSON.stringify(detail);
    }
    
    // Если есть message
    if (data.message) {
      return typeof data.message === 'string' ? data.message : JSON.stringify(data.message);
    }
  }

  // Если есть message в error
  if (error.message) {
    return error.message;
  }

  // В остальных случаях возвращаем JSON
  return JSON.stringify(error);
};


