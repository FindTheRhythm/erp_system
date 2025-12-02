import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface InventoryOperation {
  id: number;
  operation_type: string;
  sku_id: number;
  sku_name: string;
  quantity_value: number;
  quantity_unit: string;
  weight_value: number;
  weight_unit: string;
  delta_value: number;
  delta_unit: string;
  source_location?: string;
  target_location?: string;
  created_at: string;
}

export interface SKUTotal {
  id: number;
  sku_id: number;
  sku_name: string;
  total_quantity: number;
  total_weight: number;
  updated_at: string;
}

export interface LocationTotal {
  id: number;
  sku_id: number;
  sku_name: string;
  location_name: string;
  quantity: number;
  weight: number;
  updated_at: string;
}

export interface OperationCreate {
  operation_type: string;
  sku_id: number;
  quantity_value: number;
  quantity_unit: string;
  weight_value: number;
  weight_unit: string;
  source_location?: string;
  target_location?: string;
}

const inventoryApi = axios.create({
  baseURL: `${API_URL}/inventory`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const inventoryService = {
  // Operations
  getOperations: async (params?: {
    skip?: number;
    limit?: number;
    operation_type?: string;
    sku_id?: number;
    location?: string;
  }): Promise<InventoryOperation[]> => {
    const response = await inventoryApi.get<InventoryOperation[]>('/operations', { params });
    return response.data;
  },

  createOperation: async (operation: OperationCreate): Promise<InventoryOperation> => {
    const response = await inventoryApi.post<InventoryOperation>('/operations', operation);
    return response.data;
  },

  getSKUHistory: async (skuId: number, params?: {
    skip?: number;
    limit?: number;
  }): Promise<InventoryOperation[]> => {
    const response = await inventoryApi.get<InventoryOperation[]>(`/sku/${skuId}/history`, { params });
    return response.data;
  },

  // SKU Totals
  getSKUTotals: async (params?: {
    skip?: number;
    limit?: number;
    sku_id?: number;
  }): Promise<SKUTotal[]> => {
    const response = await inventoryApi.get<SKUTotal[]>('/sku/totals', { params });
    return response.data;
  },

  // Location Totals
  getLocationTotals: async (params?: {
    skip?: number;
    limit?: number;
    location_name?: string;
    sku_id?: number;
  }): Promise<LocationTotal[]> => {
    const response = await inventoryApi.get<LocationTotal[]>('/locations', { params });
    return response.data;
  },

  getLocationTotalsByLocation: async (locationName: string): Promise<LocationTotal[]> => {
    const response = await inventoryApi.get<LocationTotal[]>(`/locations/${locationName}`);
    return response.data;
  },
};


