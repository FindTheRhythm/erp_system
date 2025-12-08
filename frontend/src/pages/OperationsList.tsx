import React, { useState, useEffect, useCallback } from 'react';
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
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Pagination,
} from '@mui/material';
import { Search } from '@mui/icons-material';
import Layout from '../components/Layout';
import { inventoryService, InventoryOperation } from '../api/inventory';
import { formatApiError } from '../utils/errorHandler';

const OPERATION_TYPES: Record<string, string> = {
  create: 'Создание',
  update: 'Изменение',
  delete: 'Удаление',
  receipt: 'Прием',
  write_off: 'Списание',
  transfer: 'Перемещение',
};

const OperationsList: React.FC = () => {
  const [operations, setOperations] = useState<InventoryOperation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [operationTypeFilter, setOperationTypeFilter] = useState<string>('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const itemsPerPage = 20;

  const loadOperations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = {
        skip: (page - 1) * itemsPerPage,
        limit: itemsPerPage,
      };
      if (operationTypeFilter !== 'all') {
        params.operation_type = operationTypeFilter;
      }
      const data = await inventoryService.getOperations(params);
      setOperations(data);
      // В реальном приложении здесь должна быть информация о total из API
      setTotalPages(Math.ceil(data.length / itemsPerPage) || 1);
    } catch (err: any) {
      setError(formatApiError(err) || 'Ошибка загрузки операций');
    } finally {
      setLoading(false);
    }
  }, [page, operationTypeFilter]);

  useEffect(() => {
    loadOperations();
  }, [loadOperations]);

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const filteredOperations = operations.filter(
    (op) =>
      op.sku_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      op.sku_id.toString().includes(searchTerm) ||
      (op.source_location && op.source_location.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (op.target_location && op.target_location.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const getOperationTypeColor = (type: string): 'default' | 'primary' | 'success' | 'warning' | 'error' => {
    switch (type) {
      case 'receipt':
      case 'create':
        return 'success';
      case 'write_off':
      case 'delete':
        return 'error';
      case 'transfer':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatDeltaValue = (value: number, unit: string): string => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value} ${unit}`;
  };

  // Конвертация количества в штуки
  const convertToPieces = (value: number, unit: string): number => {
    const coefficients: Record<string, number> = {
      'шт': 1,
      'уп': 4,
      'ящ': 12,
      'пал': 36
    };
    const coefficient = coefficients[unit.toLowerCase()] || 1;
    return value * coefficient;
  };

  // Конвертация веса в килограммы
  const convertToKilograms = (value: number, unit: string): number => {
    const coefficients: Record<string, number> = {
      'т': 1000,
      'кг': 1,
      'г': 0.001
    };
    const coefficient = coefficients[unit.toLowerCase()] || 1;
    return value * coefficient;
  };

  return (
    <Layout>
      <Container maxWidth="xl">
        <Box sx={{ mb: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            История операций
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Просмотр всех операций с товарами: прием, списание, перемещение и др.
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Paper sx={{ mb: 3, p: 2 }}>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
            <TextField
              placeholder="Поиск по товару, ID, локации..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
              sx={{ flexGrow: 1, minWidth: 300 }}
            />
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Тип операции</InputLabel>
              <Select
                value={operationTypeFilter}
                label="Тип операции"
                onChange={(e) => {
                  setOperationTypeFilter(e.target.value);
                  setPage(1);
                }}
              >
                <MenuItem value="all">Все</MenuItem>
                {Object.entries(OPERATION_TYPES).map(([key, label]) => (
                  <MenuItem key={key} value={key}>
                    {label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Paper>

        <Paper>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Дата/Время</TableCell>
                  <TableCell>Тип операции</TableCell>
                  <TableCell>ID товара</TableCell>
                  <TableCell>Название товара</TableCell>
                  <TableCell align="right">Количество</TableCell>
                  <TableCell align="right">Вес</TableCell>
                  <TableCell align="right">Итоговое значение</TableCell>
                  <TableCell>Начальная локация</TableCell>
                  <TableCell>Конечная локация</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center">
                      <CircularProgress />
                    </TableCell>
                  </TableRow>
                ) : filteredOperations.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center">
                      <Typography variant="body2" color="text.secondary">
                        Нет операций
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredOperations.map((op) => (
                    <TableRow key={op.id} hover>
                      <TableCell>
                        {new Date(op.created_at).toLocaleString('ru-RU')}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={OPERATION_TYPES[op.operation_type] || op.operation_type}
                          size="small"
                          color={getOperationTypeColor(op.operation_type)}
                        />
                      </TableCell>
                      <TableCell>{op.sku_id}</TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {op.sku_name}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        {convertToPieces(op.quantity_value, op.quantity_unit).toLocaleString('ru-RU')} шт
                      </TableCell>
                      <TableCell align="right">
                        {convertToKilograms(op.weight_value, op.weight_unit).toLocaleString('ru-RU', { 
                          minimumFractionDigits: 3,
                          maximumFractionDigits: 3 
                        })} кг
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={formatDeltaValue(op.delta_value, op.delta_unit)}
                          size="small"
                          color={op.delta_value >= 0 ? 'success' : 'error'}
                        />
                      </TableCell>
                      <TableCell>{op.source_location || '-'}</TableCell>
                      <TableCell>{op.target_location || op.source_location || '-'}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
          {!loading && filteredOperations.length > 0 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={handlePageChange}
                color="primary"
              />
            </Box>
          )}
        </Paper>
      </Container>
    </Layout>
  );
};

export default OperationsList;


