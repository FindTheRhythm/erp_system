import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  console.log('Login: Component rendered, isAuthenticated=', isAuthenticated, 'isLoading=', isLoading);

  useEffect(() => {
    // Если уже авторизован, редирект на главную
    // Но только если это не первый рендер (чтобы избежать бесконечного редиректа)
    if (!isLoading && isAuthenticated) {
      console.log('Login: User is authenticated, redirecting to /');
      // Используем setTimeout чтобы избежать конфликтов с роутингом
      const timer = setTimeout(() => {
        navigate('/', { replace: true });
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isAuthenticated, isLoading, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(username, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Ошибка входа');
    } finally {
      setLoading(false);
    }
  };

  // Показывать загрузку пока проверяется авторизация
  if (isLoading) {
    return (
      <Container component="main" maxWidth="xs">
        <Box
          sx={{
            marginTop: 8,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '50vh',
          }}
        >
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper elevation={3} sx={{ padding: 4, width: '100%' }}>
          <Typography component="h1" variant="h5" align="center" gutterBottom>
            Вход в систему
          </Typography>
          <Typography variant="body2" align="center" color="text.secondary" sx={{ mb: 3 }}>
            ERP System - Управление складскими запасами
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Логин"
              name="username"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUsername(e.target.value)}
              disabled={loading}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Пароль"
              type="password"
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
              disabled={loading}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Войти'}
            </Button>
          </Box>

          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" display="block" color="text.secondary">
              Тестовые пользователи:
            </Typography>
            <Typography variant="caption" display="block" color="text.secondary">
              admin / admin (Администратор)
            </Typography>
            <Typography variant="caption" display="block" color="text.secondary">
              viewer / viewer (Просмотр)
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default Login;

