import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  message: string;
  role: 'admin' | 'viewer' | null;
}

export interface LogoutRequest {
  username: string;
  role: string;
}

export interface LogoutResponse {
  success: boolean;
  message: string;
}

const authApi = axios.create({
  baseURL: `${API_URL}/auth`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const authService = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const response = await authApi.post<LoginResponse>('/login', {
      username,
      password,
    });
    return response.data;
  },

  logout: async (username: string, role: string): Promise<LogoutResponse> => {
    const response = await authApi.post<LogoutResponse>('/logout', {
      username,
      role,
    });
    return response.data;
  },
};

