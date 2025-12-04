import React from 'react';
import { Typography, Box, Paper, Grid } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/Layout';
import { Inventory, ShoppingCart, Warehouse, Assignment, History } from '@mui/icons-material';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const menuCards = [
    {
      title: 'Каталог товаров',
      description: 'Управление товарами (SKU)',
      path: '/catalog',
      icon: <Inventory sx={{ fontSize: 40 }} />,
      color: '#1976d2',
    },
    {
      title: 'Остатки',
      description: 'Учет остатков товаров',
      path: '/inventory',
      icon: <Assignment sx={{ fontSize: 40 }} />,
      color: '#9c27b0',
    },
    {
      title: 'История операций',
      description: 'Просмотр всех операций с товарами',
      path: '/inventory/operations',
      icon: <History sx={{ fontSize: 40 }} />,
      color: '#ed6c02',
    },
    // Будут добавлены позже:
    // { title: 'Склад', description: 'Управление складами и локациями', path: '/warehouse', icon: <Warehouse />, color: '#2e7d32' },
    // { title: 'Заказы', description: 'Управление заказами', path: '/orders', icon: <ShoppingCart />, color: '#ed6c02' },
  ];

  return (
    <Layout>
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Добро пожаловать, {user?.username}!
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Система управления складскими запасами и логистикой
        </Typography>
        
        <Grid container spacing={3}>
          {menuCards.map((card) => (
            <Grid item xs={12} sm={6} md={4} key={card.path}>
              <Paper
                sx={{
                  p: 3,
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                }}
                onClick={() => navigate(card.path)}
              >
                <Box sx={{ color: card.color, mb: 2 }}>
                  {card.icon}
                </Box>
                <Typography variant="h6" component="h2" gutterBottom>
                  {card.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {card.description}
                </Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Box>
    </Layout>
  );
};

export default Dashboard;

