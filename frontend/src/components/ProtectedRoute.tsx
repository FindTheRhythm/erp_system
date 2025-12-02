import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { CircularProgress, Box } from '@mui/material';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  console.log('ProtectedRoute: isLoading=', isLoading, 'isAuthenticated=', isAuthenticated);

  // Показывать загрузку пока проверяется авторизация
  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  // Если не авторизован - редирект на /login
  if (!isAuthenticated) {
    console.log('ProtectedRoute: Not authenticated, redirecting to /login');
    return <Navigate to="/login" replace />;
  }

  // Авторизован - показать защищенный контент
  console.log('ProtectedRoute: Authenticated, showing content');
  return <>{children}</>;
};

export default ProtectedRoute;

