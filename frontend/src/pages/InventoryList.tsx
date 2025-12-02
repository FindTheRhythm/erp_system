import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  InputAdornment,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Chip,
} from '@mui/material';
import { Search } from '@mui/icons-material';
import Layout from '../components/Layout';
import { inventoryService, SKUTotal, LocationTotal } from '../api/inventory';
import { catalogService, SKUList } from '../api/catalog';
import { formatApiError } from '../utils/errorHandler';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`inventory-tabpanel-${index}`}
      aria-labelledby={`inventory-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const InventoryList: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [skuTotals, setSkuTotals] = useState<SKUTotal[]>([]);
  const [locationTotals, setLocationTotals] = useState<LocationTotal[]>([]);
  const [skus, setSkus] = useState<SKUList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [skuData, locationData, skusData] = await Promise.all([
        inventoryService.getSKUTotals(),
        inventoryService.getLocationTotals(),
        catalogService.getSKUs(), // Получаем список товаров для фильтрации по статусу
      ]);
      setSkuTotals(skuData);
      setLocationTotals(locationData);
      setSkus(skusData);
    } catch (err: any) {
      setError(formatApiError(err) || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Фильтруем остатки: показываем только товары со статусом "available" (есть)
  const availableSkuIds = new Set(
    skus.filter(sku => sku.status === 'available').map(sku => sku.id)
  );

  const filteredSkuTotals = skuTotals.filter(
    (item) => {
      // Фильтр по статусу - только available
      if (!availableSkuIds.has(item.sku_id)) {
        return false;
      }
      // Фильтр по поиску
      return (
        item.sku_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.sku_id.toString().includes(searchTerm)
      );
    }
  );

  const filteredLocationTotals = locationTotals.filter(
    (item) => {
      // Фильтр по статусу - только available
      if (!availableSkuIds.has(item.sku_id)) {
        return false;
      }
      // Фильтр по поиску
      return (
        item.sku_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.location_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.sku_id.toString().includes(searchTerm)
      );
    }
  );

  // Группируем остатки по локациям
  const locationGroups = filteredLocationTotals.reduce((acc, item) => {
    if (!acc[item.location_name]) {
      acc[item.location_name] = [];
    }
    acc[item.location_name].push(item);
    return acc;
  }, {} as Record<string, LocationTotal[]>);

  return (
    <Layout>
      <Container maxWidth="xl">
        <Box sx={{ mb: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Остатки товаров
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Просмотр абсолютных остатков по товарам и остатков по локациям
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Paper sx={{ mb: 3 }}>
          <TextField
            fullWidth
            placeholder="Поиск по названию товара, ID или локации..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
            sx={{ p: 2 }}
          />
        </Paper>

        <Paper>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="inventory tabs">
              <Tab label="Абсолютные остатки (по SKU)" />
              <Tab label="Остатки по локациям" />
            </Tabs>
          </Box>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              <TabPanel value={tabValue} index={0}>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>ID товара</TableCell>
                        <TableCell>Название товара</TableCell>
                        <TableCell align="right">Общее количество</TableCell>
                        <TableCell align="right">Общий вес (кг)</TableCell>
                        <TableCell>Обновлено</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {filteredSkuTotals.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={5} align="center">
                            <Typography variant="body2" color="text.secondary">
                              Нет данных об остатках
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ) : (
                        filteredSkuTotals.map((item) => (
                          <TableRow key={item.id} hover>
                            <TableCell>{item.sku_id}</TableCell>
                            <TableCell>
                              <Typography variant="body2" fontWeight="medium">
                                {item.sku_name}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">{item.total_quantity}</TableCell>
                            <TableCell align="right">
                              <Chip
                                label={`${item.total_weight} кг`}
                                size="small"
                                color={item.total_weight > 0 ? 'success' : 'default'}
                              />
                            </TableCell>
                            <TableCell>
                              {new Date(item.updated_at).toLocaleString('ru-RU')}
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </TabPanel>

              <TabPanel value={tabValue} index={1}>
                {Object.keys(locationGroups).length === 0 ? (
                  <Box sx={{ p: 3, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Нет данных об остатках по локациям
                    </Typography>
                  </Box>
                ) : (
                  Object.entries(locationGroups).map(([locationName, items]) => (
                    <Box key={locationName} sx={{ mb: 4 }}>
                      <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
                        Локация: {locationName}
                      </Typography>
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>ID товара</TableCell>
                              <TableCell>Название товара</TableCell>
                              <TableCell align="right">Количество</TableCell>
                              <TableCell align="right">Вес (кг)</TableCell>
                              <TableCell>Обновлено</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {items.map((item) => (
                              <TableRow key={item.id} hover>
                                <TableCell>{item.sku_id}</TableCell>
                                <TableCell>
                                  <Typography variant="body2" fontWeight="medium">
                                    {item.sku_name}
                                  </Typography>
                                </TableCell>
                                <TableCell align="right">{item.quantity}</TableCell>
                                <TableCell align="right">
                                  <Chip
                                    label={`${item.weight} кг`}
                                    size="small"
                                    color={item.weight > 0 ? 'success' : 'default'}
                                  />
                                </TableCell>
                                <TableCell>
                                  {new Date(item.updated_at).toLocaleString('ru-RU')}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Box>
                  ))
                )}
              </TabPanel>
            </>
          )}
        </Paper>
      </Container>
    </Layout>
  );
};

export default InventoryList;

