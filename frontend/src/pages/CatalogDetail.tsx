import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Grid,
  IconButton,
} from '@mui/material';
import { Edit, ArrowBack } from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { catalogService, SKU } from '../api/catalog';
import Layout from '../components/Layout';
import { formatApiError } from '../utils/errorHandler';

const CatalogDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const isAdmin = user?.role === 'admin';

  const [sku, setSku] = useState<SKU | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (id) {
      loadSKU(parseInt(id));
    }
  }, [id]);

  const loadSKU = async (skuId: number) => {
    try {
      setLoading(true);
      setError('');
      const data = await catalogService.getSKU(skuId);
      setSku(data);
    } catch (err: any) {
      setError(formatApiError(err) || 'Ошибка загрузки товара');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'available':
        return 'success';
      case 'unavailable':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status?: string) => {
    switch (status) {
      case 'available':
        return 'Есть';
      case 'unavailable':
        return 'Отсутствует';
      case 'unknown':
        return 'Неизвестно';
      default:
        return 'Неизвестно';
    }
  };

  if (loading) {
    return (
      <Layout>
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      </Layout>
    );
  }

  if (error || !sku) {
    return (
      <Layout>
        <Box>
          <Alert severity="error">{error || 'Товар не найден'}</Alert>
          <Button startIcon={<ArrowBack />} onClick={() => navigate('/catalog')} sx={{ mt: 2 }}>
            Вернуться к списку
          </Button>
        </Box>
      </Layout>
    );
  }

  return (
    <Layout>
      <Box>
        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={() => navigate('/catalog')}>
            <ArrowBack />
          </IconButton>
          <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
            {sku.name}
          </Typography>
          {isAdmin && (
            <Button
              variant="contained"
              startIcon={<Edit />}
              onClick={() => navigate(`/catalog/${sku.id}/edit`)}
            >
              Редактировать
            </Button>
          )}
        </Box>

        <Paper sx={{ p: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Артикул
              </Typography>
              <Typography variant="body1" sx={{ mb: 2 }}>
                {sku.code}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Статус
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Chip
                  label={getStatusLabel(sku.status)}
                  color={getStatusColor(sku.status) as any}
                />
              </Box>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Вес
              </Typography>
              <Typography variant="body1" sx={{ mb: 2 }}>
                {sku.weight} {sku.weight_unit?.name || ''}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Количество
              </Typography>
              <Typography variant="body1" sx={{ mb: 2 }}>
                {sku.quantity} {sku.quantity_unit?.name || ''}
              </Typography>
            </Grid>
            {sku.price && (
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Цена
                </Typography>
                <Typography variant="body1" sx={{ mb: 2 }}>
                  {sku.price} {sku.price_unit?.name || ''}
                </Typography>
              </Grid>
            )}
            {sku.description && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary">
                  Описание
                </Typography>
                <Typography variant="body1" sx={{ mb: 2 }}>
                  {sku.description}
                </Typography>
              </Grid>
            )}
            {sku.photo_url && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary">
                  Фото
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <img
                    src={sku.photo_url}
                    alt={sku.name}
                    style={{ maxWidth: '100%', height: 'auto', maxHeight: 300 }}
                  />
                </Box>
              </Grid>
            )}
          </Grid>
        </Paper>
      </Box>
    </Layout>
  );
};

export default CatalogDetail;

