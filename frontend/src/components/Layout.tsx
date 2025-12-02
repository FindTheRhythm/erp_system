import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Divider,
} from '@mui/material';
import {
  Home,
  Inventory,
  ShoppingCart,
  Warehouse,
  Assignment,
  Notifications,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // Определяем активный пункт меню (проверяем начало пути)
  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    // Точное совпадение
    if (location.pathname === path) {
      return true;
    }
    // Если текущий путь начинается с path, проверяем что следующий символ - это / или конец строки
    // Это нужно чтобы /inventory не был активен для /inventory/operations
    if (location.pathname.startsWith(path)) {
      const nextChar = location.pathname[path.length];
      // Если следующий символ - это / или конец строки, то путь активен
      return nextChar === '/' || nextChar === undefined;
    }
    return false;
  };

  const menuItems = [
    { text: 'Главная', path: '/', icon: <Home /> },
    { text: 'Каталог товаров', path: '/catalog', icon: <Inventory /> },
    { text: 'Остатки', path: '/inventory', icon: <Assignment /> },
    { text: 'Операции', path: '/inventory/operations', icon: <Warehouse /> },
    // Будут добавлены позже:
    // { text: 'Склад', path: '/warehouse', icon: <Warehouse /> },
    // { text: 'Заказы', path: '/orders', icon: <ShoppingCart /> },
    // { text: 'Уведомления', path: '/notifications', icon: <Notifications /> },
  ];

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, cursor: 'pointer' }} onClick={() => navigate('/')}>
            ERP System
          </Typography>
          <Typography variant="body2" sx={{ mr: 2 }}>
            {user?.username} ({user?.role === 'admin' ? 'Администратор' : 'Просмотр'})
          </Typography>
          <Button color="inherit" onClick={handleLogout}>
            Выход
          </Button>
        </Toolbar>
      </AppBar>
      <Box sx={{ display: 'flex' }}>
        <Drawer
          variant="permanent"
          sx={{
            width: 240,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: 240,
              boxSizing: 'border-box',
              borderRight: '1px solid rgba(0, 0, 0, 0.12)',
            },
          }}
        >
          <Toolbar />
          <Divider />
          <List>
            {menuItems.map((item) => (
              <ListItem key={item.path} disablePadding>
                <ListItemButton
                  selected={isActive(item.path)}
                  onClick={() => navigate(item.path)}
                  sx={{
                    '&.Mui-selected': {
                      backgroundColor: 'primary.main',
                      color: 'primary.contrastText',
                      '&:hover': {
                        backgroundColor: 'primary.dark',
                      },
                      '& .MuiListItemIcon-root': {
                        color: 'primary.contrastText',
                      },
                    },
                    '&:hover': {
                      backgroundColor: 'action.hover',
                    },
                  }}
                >
                  <ListItemIcon
                    sx={{
                      minWidth: 40,
                      color: isActive(item.path) ? 'inherit' : 'inherit',
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Drawer>
        <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
          {children}
        </Box>
      </Box>
    </>
  );
};

export default Layout;

