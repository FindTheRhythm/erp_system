import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService, LoginResponse } from '../api/auth';

interface User {
  username: string;
  role: 'admin' | 'viewer';
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Проверить сохраненную сессию при загрузке
    const savedUser = localStorage.getItem('user');
    console.log('AuthContext: Checking saved user:', savedUser);
    
    if (savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser);
        // Валидация данных пользователя
        if (parsedUser && parsedUser.username && parsedUser.role && 
            (parsedUser.role === 'admin' || parsedUser.role === 'viewer')) {
          console.log('AuthContext: Valid user found:', parsedUser);
          setUser(parsedUser);
        } else {
          // Невалидные данные - удаляем
          console.log('AuthContext: Invalid user data, removing');
          localStorage.removeItem('user');
        }
      } catch (e) {
        // Ошибка парсинга - удаляем
        console.error('AuthContext: Error parsing user data:', e);
        localStorage.removeItem('user');
      }
    } else {
      console.log('AuthContext: No saved user found');
    }
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string): Promise<void> => {
    try {
      const response: LoginResponse = await authService.login(username, password);
      
      if (response.success && response.role) {
        const userData: User = {
          username,
          role: response.role,
        };
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
      } else {
        throw new Error(response.message || 'Ошибка входа');
      }
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error(error.message || 'Ошибка подключения к серверу');
    }
  };

  const logout = async (): Promise<void> => {
    if (user) {
      try {
        await authService.logout(user.username, user.role);
      } catch (error) {
        console.error('Ошибка при выходе:', error);
      }
    }
    setUser(null);
    localStorage.removeItem('user');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        isAuthenticated: !!user,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

