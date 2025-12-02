import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface Unit {
  id: number;
  name: string;
  type: 'weight' | 'quantity' | 'price';
  description?: string;
}

export interface SKU {
  id: number;
  code: string;
  name: string;
  weight: string;
  weight_unit_id: number;
  quantity: string;
  quantity_unit_id: number;
  description?: string;
  price?: string;
  price_unit_id?: number;
  status?: 'available' | 'unavailable' | 'unknown';
  photo_url?: string;
  weight_unit?: Unit;
  quantity_unit?: Unit;
  price_unit?: Unit;
}

export interface SKUList {
  id: number;
  code: string;
  name: string;
  weight: string;
  quantity: string;
  status?: 'available' | 'unavailable' | 'unknown';
}

export interface SKUCreate {
  code: string;
  name: string;
  weight: string;
  weight_unit_id: number;
  quantity: string;
  quantity_unit_id: number;
  description?: string;
  price?: string;
  price_unit_id?: number;
  status?: 'available' | 'unavailable' | 'unknown';
  photo_url?: string;
}

export interface SKUUpdate {
  name?: string;
  weight?: string;
  weight_unit_id?: number;
  quantity?: string;
  quantity_unit_id?: number;
  description?: string;
  price?: string;
  price_unit_id?: number;
  status?: 'available' | 'unavailable' | 'unknown';
  photo_url?: string;
}

// Функция для получения заголовков с ролью пользователя
const getHeaders = (): { 'X-User-Role': string } => {
  const userStr = localStorage.getItem('user');
  if (userStr) {
    try {
      const user = JSON.parse(userStr);
      return { 'X-User-Role': user.role || 'viewer' };
    } catch (e) {
      return { 'X-User-Role': 'viewer' };
    }
  }
  return { 'X-User-Role': 'viewer' };
};

const catalogApi = axios.create({
  baseURL: `${API_URL}/catalog`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Добавляем interceptor для добавления заголовка с ролью
catalogApi.interceptors.request.use((config) => {
  const headers = getHeaders();
  if (config.headers) {
    // Используем правильный способ установки заголовков в Axios
    Object.assign(config.headers, headers);
  }
  return config;
});

export const catalogService = {
  // Units
  getUnits: async (type?: 'weight' | 'quantity' | 'price'): Promise<Unit[]> => {
    const params = type ? { type } : {};
    const response = await catalogApi.get<Unit[]>('/units', { params });
    return response.data;
  },

  createUnit: async (unit: Omit<Unit, 'id'>): Promise<Unit> => {
    const response = await catalogApi.post<Unit>('/units', unit);
    return response.data;
  },

  // SKUs
  getSKUs: async (params?: {
    skip?: number;
    limit?: number;
    search?: string;
    status?: 'available' | 'unavailable' | 'unknown';
  }): Promise<SKUList[]> => {
    const response = await catalogApi.get<SKUList[]>('/skus', { params });
    return response.data;
  },

  getSKU: async (id: number): Promise<SKU> => {
    const response = await catalogApi.get<SKU>(`/skus/${id}`);
    return response.data;
  },

  searchSKUs: async (q: string, limit?: number): Promise<SKUList[]> => {
    const response = await catalogApi.get<SKUList[]>('/skus/search', {
      params: { q, limit },
    });
    return response.data;
  },

  createSKU: async (sku: SKUCreate): Promise<SKU> => {
    const response = await catalogApi.post<SKU>('/skus', sku);
    return response.data;
  },

  updateSKU: async (id: number, sku: SKUUpdate): Promise<SKU> => {
    const response = await catalogApi.put<SKU>(`/skus/${id}`, sku);
    return response.data;
  },

  deleteSKU: async (id: number): Promise<void> => {
    await catalogApi.delete(`/skus/${id}`);
  },

  // CSV
  exportCSV: async (): Promise<Blob> => {
    const response = await catalogApi.get('/skus/export/csv', {
      responseType: 'blob',
    });
    return response.data;
  },

  importCSV: async (file: File): Promise<{ imported: number; errors: string[]; message: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await catalogApi.post('/skus/import/csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

