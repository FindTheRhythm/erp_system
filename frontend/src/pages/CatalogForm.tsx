import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { catalogService, SKUCreate, SKUUpdate, Unit } from '../api/catalog';
import Layout from '../components/Layout';
import { formatApiError } from '../utils/errorHandler';

const CatalogForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const isEdit = !!id;
  const isAdmin = user?.role === 'admin';

  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(isEdit);
  const [error, setError] = useState<string>('');
  const [units, setUnits] = useState<Unit[]>([]);
  
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    weight: '1',  // Значение по умолчанию
    weight_unit_id: '',
    quantity: '1',  // Значение по умолчанию
    quantity_unit_id: '',
    description: '',
    price: '',
    price_unit_id: '',
    status: 'unknown' as 'available' | 'unavailable' | 'unknown',
    photo_url: '',
  });

  useEffect(() => {
    loadUnits();
    if (isEdit && id) {
      loadSKU(parseInt(id));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, isEdit]);

  // Устанавливаем значения по умолчанию после загрузки единиц измерения
  useEffect(() => {
    if (!isEdit && units.length > 0 && !formData.weight_unit_id && !formData.quantity_unit_id) {
      // Находим единицы измерения "кг" и "шт"
      const kgUnit = units.find(u => u.type === 'weight' && u.name === 'кг');
      const pcsUnit = units.find(u => u.type === 'quantity' && u.name === 'шт');
      
      // Устанавливаем значения по умолчанию
      if (kgUnit && pcsUnit) {
        setFormData(prev => ({
          ...prev,
          weight: '1',
          weight_unit_id: kgUnit.id.toString(),
          quantity: '1',
          quantity_unit_id: pcsUnit.id.toString(),
        }));
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [units, isEdit]);

  const loadUnits = async () => {
    try {
      const data = await catalogService.getUnits();
      setUnits(data);
    } catch (err: any) {
      setError(formatApiError(err) || 'Ошибка загрузки единиц измерения');
    }
  };

  const loadSKU = async (skuId: number) => {
    try {
      setLoadingData(true);
      const sku = await catalogService.getSKU(skuId);
      setFormData({
        code: sku.code,
        name: sku.name,
        weight: sku.weight,
        weight_unit_id: sku.weight_unit_id.toString(),
        quantity: sku.quantity,
        quantity_unit_id: sku.quantity_unit_id.toString(),
        description: sku.description || '',
        price: sku.price || '',
        price_unit_id: sku.price_unit_id?.toString() || '',
        status: (sku.status || 'unknown') as 'available' | 'unavailable' | 'unknown',
        photo_url: sku.photo_url || '',
      });
    } catch (err: any) {
      setError(formatApiError(err) || 'Ошибка загрузки товара');
    } finally {
      setLoadingData(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAdmin) {
      setError('Доступ запрещен. Требуется роль администратора');
      return;
    }

    try {
      setLoading(true);
      setError('');

      if (isEdit && id) {
        const updateData: SKUUpdate = {
          name: formData.name,
          weight: formData.weight,
          weight_unit_id: parseInt(formData.weight_unit_id),
          quantity: formData.quantity,
          quantity_unit_id: parseInt(formData.quantity_unit_id),
          description: formData.description || undefined,
          price: formData.price || undefined,
          price_unit_id: formData.price_unit_id ? parseInt(formData.price_unit_id) : undefined,
          status: formData.status,
          photo_url: formData.photo_url || undefined,
        };
        await catalogService.updateSKU(parseInt(id), updateData);
      } else {
        const createData: SKUCreate = {
          code: formData.code.toUpperCase(),
          name: formData.name,
          weight: formData.weight,
          weight_unit_id: parseInt(formData.weight_unit_id),
          quantity: formData.quantity,
          quantity_unit_id: parseInt(formData.quantity_unit_id),
          description: formData.description || undefined,
          price: formData.price || undefined,
          price_unit_id: formData.price_unit_id ? parseInt(formData.price_unit_id) : undefined,
          status: formData.status,
          photo_url: formData.photo_url || undefined,
        };
        await catalogService.createSKU(createData);
      }

      navigate('/catalog');
    } catch (err: any) {
      setError(formatApiError(err) || 'Ошибка сохранения товара');
    } finally {
      setLoading(false);
    }
  };

  const weightUnits = units.filter(u => u.type === 'weight');
  const quantityUnits = units.filter(u => u.type === 'quantity');
  const priceUnits = units.filter(u => u.type === 'price');

  if (loadingData) {
    return (
      <Layout>
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      </Layout>
    );
  }

  return (
    <Layout>
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          {isEdit ? 'Редактирование товара' : 'Создание товара'}
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {!isAdmin && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            У вас нет прав для создания/редактирования товаров
          </Alert>
        )}

        <Paper sx={{ p: 3 }}>
          <form onSubmit={handleSubmit}>
            {!isEdit && (
              <TextField
                fullWidth
                label="Артикул (XXXX-XXXX)"
                value={formData.code}
                onChange={(e) => {
                  let value = e.target.value.toUpperCase();
                  // Удаляем все символы кроме букв и цифр
                  value = value.replace(/[^A-Z0-9]/g, '');
                  
                  // Автоматически форматируем: если больше 4 символов, добавляем дефис
                  if (value.length > 4) {
                    value = value.slice(0, 4) + '-' + value.slice(4, 8);
                  }
                  
                  // Ограничиваем до 8 символов (4+4)
                  if (value.length > 9) {
                    value = value.slice(0, 9);
                  }
                  
                  setFormData({ ...formData, code: value });
                }}
                required
                disabled={!isAdmin}
                helperText="Введите артикул (буквы и цифры, автоматически форматируется в XXXX-XXXX)"
                sx={{ mb: 2 }}
              />
            )}

            <TextField
              fullWidth
              label="Название"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              disabled={!isAdmin}
              inputProps={{ maxLength: 15 }}
              helperText={`${formData.name.length}/15 символов`}
              sx={{ mb: 2 }}
            />

            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <TextField
                fullWidth
                label="Вес"
                value={formData.weight}
                onChange={(e) => setFormData({ ...formData, weight: e.target.value })}
                required
                disabled={!isAdmin}
                inputProps={{ maxLength: 5 }}
              />
              <FormControl fullWidth required disabled={!isAdmin}>
                <InputLabel>Единица веса</InputLabel>
                <Select
                  value={formData.weight_unit_id}
                  label="Единица веса"
                  onChange={(e) => setFormData({ ...formData, weight_unit_id: e.target.value })}
                >
                  {weightUnits.map((unit) => (
                    <MenuItem key={unit.id} value={unit.id.toString()}>
                      {unit.name} - {unit.description}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>

            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <TextField
                fullWidth
                label="Количество"
                value={formData.quantity}
                onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                required
                disabled={!isAdmin}
                inputProps={{ maxLength: 5 }}
              />
              <FormControl fullWidth required disabled={!isAdmin}>
                <InputLabel>Единица количества</InputLabel>
                <Select
                  value={formData.quantity_unit_id}
                  label="Единица количества"
                  onChange={(e) => setFormData({ ...formData, quantity_unit_id: e.target.value })}
                >
                  {quantityUnits.map((unit) => (
                    <MenuItem key={unit.id} value={unit.id.toString()}>
                      {unit.name} - {unit.description}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>

            <TextField
              fullWidth
              label="Описание"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              multiline
              rows={3}
              disabled={!isAdmin}
              inputProps={{ maxLength: 120 }}
              helperText={`${formData.description.length}/120 символов`}
              sx={{ mb: 2 }}
            />

            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <TextField
                fullWidth
                label="Цена"
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                disabled={!isAdmin}
                inputProps={{ maxLength: 5 }}
              />
              <FormControl fullWidth disabled={!isAdmin}>
                <InputLabel>Единица цены</InputLabel>
                <Select
                  value={formData.price_unit_id}
                  label="Единица цены"
                  onChange={(e) => setFormData({ ...formData, price_unit_id: e.target.value })}
                >
                  <MenuItem value="">Не указано</MenuItem>
                  {priceUnits.map((unit) => (
                    <MenuItem key={unit.id} value={unit.id.toString()}>
                      {unit.name} - {unit.description}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>

            <FormControl fullWidth sx={{ mb: 2 }} disabled={!isAdmin}>
              <InputLabel>Статус</InputLabel>
              <Select
                value={formData.status}
                label="Статус"
                onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
              >
                <MenuItem value="available">Есть</MenuItem>
                <MenuItem value="unavailable">Отсутствует</MenuItem>
                <MenuItem value="unknown">Неизвестно</MenuItem>
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Ссылка на фото"
              value={formData.photo_url}
              onChange={(e) => setFormData({ ...formData, photo_url: e.target.value })}
              disabled={!isAdmin}
              sx={{ mb: 2 }}
            />

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button variant="outlined" onClick={() => navigate('/catalog')}>
                Отмена
              </Button>
              {isAdmin && (
                <Button type="submit" variant="contained" disabled={loading}>
                  {loading ? <CircularProgress size={24} /> : isEdit ? 'Сохранить' : 'Создать'}
                </Button>
              )}
            </Box>
          </form>
        </Paper>
      </Box>
    </Layout>
  );
};

export default CatalogForm;

