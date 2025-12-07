import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export type LocationType = 'storage' | 'warehouse' | 'temp_storage';

export type OperationType = 
  | 'receipt' 
  | 'shipment' 
  | 'transfer'
  | 'global_distribution_all'
  | 'global_distribution_sku'
  | 'replenishment_all'
  | 'replenishment_sku'
  | 'placement_all'
  | 'placement_sku';

export interface Location {
  id: number;
  name: string;
  type: LocationType;
  max_capacity_kg: number;
  current_capacity_kg: number;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface LocationStats {
  id: number;
  name: string;
  type: LocationType;
  max_capacity_kg: number;
  current_capacity_kg: number;
  usage_percent: number;
  description?: string;
}

export interface WarehouseOperation {
  id: number;
  operation_type: OperationType;
  sku_id?: number;
  sku_name?: string;
  source_location_id?: number;
  target_location_id?: number;
  quantity_kg: number;
  status: 'pending' | 'completed' | 'failed';
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface WarehouseOperationCreate {
  operation_type: OperationType;
  sku_id?: number;
  source_location_id?: number;
  target_location_id?: number;
}

export interface TempStorageItem {
  id: number;
  sku_id: number;
  sku_name: string;
  quantity_kg: number;
  source_operation_id?: number;
  created_at: string;
  moved_to_storage_at?: string;
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

const warehouseApi = axios.create({
  baseURL: `${API_URL}/warehouse`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Добавляем interceptor для добавления заголовка с ролью
warehouseApi.interceptors.request.use((config) => {
  const headers = getHeaders();
  if (config.headers) {
    Object.assign(config.headers, headers);
  }
  return config;
});

export const warehouseService = {
  // Locations
  getLocations: async (): Promise<Location[]> => {
    const response = await warehouseApi.get<Location[]>('/locations');
    return response.data;
  },

  getLocation: async (locationId: number): Promise<Location> => {
    const response = await warehouseApi.get<Location>(`/locations/${locationId}`);
    return response.data;
  },

  getLocationsStats: async (): Promise<LocationStats[]> => {
    const response = await warehouseApi.get<LocationStats[]>('/locations/stats');
    return response.data;
  },

  // Operations
  getOperations: async (): Promise<WarehouseOperation[]> => {
    const response = await warehouseApi.get<WarehouseOperation[]>('/operations');
    return response.data;
  },

  getOperation: async (operationId: number): Promise<WarehouseOperation> => {
    const response = await warehouseApi.get<WarehouseOperation>(`/operations/${operationId}`);
    return response.data;
  },

  createOperation: async (operation: WarehouseOperationCreate): Promise<WarehouseOperation> => {
    const response = await warehouseApi.post<WarehouseOperation>('/operations', operation);
    return response.data;
  },

  // Temp Storage
  getTempStorageItems: async (): Promise<TempStorageItem[]> => {
    const response = await warehouseApi.get<TempStorageItem[]>('/temp-storage');
    return response.data;
  },

  processTempStorage: async (): Promise<{ message: string }> => {
    const response = await warehouseApi.post<{ message: string }>('/temp-storage/process');
    return response.data;
  },
};

