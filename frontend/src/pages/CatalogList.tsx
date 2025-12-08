import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
} from '@mui/material';
import { Add, Edit, Delete, Visibility, Search, FileDownload, FileUpload } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { catalogService, SKUList } from '../api/catalog';
import Layout from '../components/Layout';
import { formatApiError } from '../utils/errorHandler';

const CatalogList: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [skus, setSkus] = useState<SKUList[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [skuToDelete, setSkuToDelete] = useState<SKUList | null>(null);
  const [error, setError] = useState<string>('');
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);

  const isAdmin = user?.role === 'admin';

  const loadSKUs = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const params: any = {
        limit: 100,
      };
      if (searchTerm) {
        params.search = searchTerm;
      }
      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }
      const data = await catalogService.getSKUs(params);
      setSkus(data);
    } catch (err: any) {
      setError(formatApiError(err) || 'Ошибка загрузки товаров');
    } finally {
      setLoading(false);
    }
  }, [searchTerm, statusFilter]);

  useEffect(() => {
    loadSKUs();
  }, [loadSKUs]);

  const handleDelete = async () => {
    if (!skuToDelete) return;
    try {
      await catalogService.deleteSKU(skuToDelete.id);
      setDeleteDialogOpen(false);
      setSkuToDelete(null);
      loadSKUs();
    } catch (err: any) {
      setError(formatApiError(err) || 'Ошибка удаления товара');
    }
  };

  const handleExport = async () => {
    try {
      const blob = await catalogService.exportCSV();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'skus_export.csv';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setError(formatApiError(err) || 'Ошибка экспорта');
    }
  };

  const handleImport = async () => {
    if (!importFile) return;
    try {
      setImporting(true);
      const result = await catalogService.importCSV(importFile);
      setImportDialogOpen(false);
      setImportFile(null);
      if (result.errors.length > 0) {
        setError(`Импортировано: ${result.imported}, Ошибок: ${result.errors.length}`);
      } else {
        setError('');
      }
      loadSKUs();
    } catch (err: any) {
      setError(formatApiError(err) || 'Ошибка импорта');
    } finally {
      setImporting(false);
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

  return (
    <Layout>
      <Box>
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h4" component="h1">
            Каталог товаров
          </Typography>
          <Box>
            {isAdmin && (
              <>
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={() => navigate('/catalog/new')}
                  sx={{ mr: 1 }}
                >
                  Создать товар
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<FileUpload />}
                  onClick={() => setImportDialogOpen(true)}
                  sx={{ mr: 1 }}
                >
                  Импорт CSV
                </Button>
              </>
            )}
            <Button
              variant="outlined"
              startIcon={<FileDownload />}
              onClick={handleExport}
            >
              Экспорт CSV
            </Button>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
          <TextField
            placeholder="Поиск по названию или артикулу"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: <Search sx={{ mr: 1, color: 'action.active' }} />,
            }}
            sx={{ flexGrow: 1 }}
          />
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Статус</InputLabel>
            <Select
              value={statusFilter}
              label="Статус"
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="all">Все</MenuItem>
              <MenuItem value="available">Есть</MenuItem>
              <MenuItem value="unavailable">Отсутствует</MenuItem>
              <MenuItem value="unknown">Неизвестно</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Артикул</TableCell>
                  <TableCell>Название</TableCell>
                  <TableCell>Вес</TableCell>
                  <TableCell>Количество</TableCell>
                  <TableCell>Статус</TableCell>
                  <TableCell align="right">Действия</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {skus.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                        Товары не найдены
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  skus.map((sku) => (
                    <TableRow key={sku.id} hover>
                      <TableCell>{sku.code}</TableCell>
                      <TableCell>{sku.name}</TableCell>
                      <TableCell>{sku.weight}</TableCell>
                      <TableCell>{sku.quantity}</TableCell>
                      <TableCell>
                        <Chip
                          label={getStatusLabel(sku.status)}
                          color={getStatusColor(sku.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={() => navigate(`/catalog/${sku.id}`)}
                          title="Просмотр"
                        >
                          <Visibility />
                        </IconButton>
                        {isAdmin && (
                          <>
                            <IconButton
                              size="small"
                              onClick={() => navigate(`/catalog/${sku.id}/edit`)}
                              title="Редактировать"
                            >
                              <Edit />
                            </IconButton>
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => {
                                setSkuToDelete(sku);
                                setDeleteDialogOpen(true);
                              }}
                              title="Удалить"
                            >
                              <Delete />
                            </IconButton>
                          </>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {/* Диалог удаления */}
        <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
          <DialogTitle>Удаление товара</DialogTitle>
          <DialogContent>
            <Typography>
              Вы уверены, что хотите удалить товар "{skuToDelete?.name}" (артикул: {skuToDelete?.code})?
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDeleteDialogOpen(false)}>Отмена</Button>
            <Button onClick={handleDelete} color="error" variant="contained">
              Удалить
            </Button>
          </DialogActions>
        </Dialog>

        {/* Диалог импорта */}
        <Dialog open={importDialogOpen} onClose={() => setImportDialogOpen(false)}>
          <DialogTitle>Импорт товаров из CSV</DialogTitle>
          <DialogContent>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setImportFile(e.target.files?.[0] || null)}
              style={{ marginTop: 16 }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setImportDialogOpen(false)}>Отмена</Button>
            <Button
              onClick={handleImport}
              variant="contained"
              disabled={!importFile || importing}
            >
              {importing ? <CircularProgress size={24} /> : 'Импортировать'}
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Layout>
  );
};

export default CatalogList;

