import React from 'react';
import { Box, Typography, Paper, List, ListItem, ListItemText } from '@mui/material';
import { LocationTotal } from '../api/inventory';

interface CircularProgressChartProps {
  value: number; // Процент заполнения (0-100)
  maxValue: number; // Максимальное значение
  currentValue: number; // Текущее значение
  label: string;
  size?: number;
  color?: string;
  items?: LocationTotal[]; // Товары для отображения
}

// Цвета для разных товаров
const ITEM_COLORS = [
  '#1976d2', '#9c27b0', '#ed6c02', '#2e7d32', '#d32f2f',
  '#0288d1', '#7b1fa2', '#f57c00', '#388e3c', '#c62828',
  '#0277bd', '#6a1b9a', '#ef6c00', '#2e7d32', '#b71c1c',
];

const CircularProgressChart: React.FC<CircularProgressChartProps> = ({
  value,
  maxValue,
  currentValue,
  label,
  size = 120,
  color = '#1976d2',
  items = [],
}) => {
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (value / 100) * circumference;
  
  // Определяем цвет в зависимости от заполнения
  let chartColor = color;
  if (value >= 90) {
    chartColor = '#d32f2f'; // Красный при переполнении
  } else if (value >= 75) {
    chartColor = '#ed6c02'; // Оранжевый при почти полном заполнении
  } else if (value >= 50) {
    chartColor = '#ed6c02'; // Оранжевый при среднем заполнении
  } else {
    chartColor = '#2e7d32'; // Зеленый при низком заполнении
  }

  // Получаем топ-10 товаров
  const topItems = [...items]
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 10);
  
  const totalWeight = currentValue || 1;
  
  // Вычисляем сегменты для каждого товара в диаграмме
  // Сегменты должны заполнять круг пропорционально заполненности локации (value%)
  const segments: Array<{ color: string; percentage: number; offset: number; length: number }> = [];
  if (topItems.length > 0 && currentValue > 0 && value > 0) {
    // Общая длина заполненной части круга (value% от полной окружности)
    const filledCircumference = (value / 100) * circumference;
    let accumulatedLength = 0;
    
    topItems.forEach((item, index) => {
      // Длина сегмента пропорциональна весу товара от заполненной части
      const segmentLength = (item.weight / currentValue) * filledCircumference;
      
      if (segmentLength > 1) { // Показываем только если длина больше 1 пикселя
        // Offset: начинаем с начала заполненной части (circumference - filledCircumference)
        // и добавляем накопленную длину предыдущих сегментов
        const segmentOffset = circumference - filledCircumference + accumulatedLength;
        
        segments.push({
          color: ITEM_COLORS[index % ITEM_COLORS.length],
          percentage: (item.weight / currentValue) * 100,
          offset: segmentOffset,
          length: segmentLength,
        });
        accumulatedLength += segmentLength;
      }
    });
  }

  return (
    <Paper
      elevation={2}
      sx={{
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'stretch',
        minHeight: size + 200,
      }}
    >
      <Typography variant="h6" gutterBottom align="center" sx={{ mb: 1 }}>
        {label}
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
        <Box sx={{ flexShrink: 0 }}>
          <Box sx={{ position: 'relative', display: 'inline-flex' }}>
            <svg width={size} height={size}>
              {/* Фоновый круг */}
              <circle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke="#e0e0e0"
                strokeWidth="12"
              />
              {/* Сегменты для каждого товара */}
              {segments.length > 0 ? (
                segments.map((segment, idx) => (
                  <circle
                    key={idx}
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    fill="none"
                    stroke={segment.color}
                    strokeWidth="12"
                    strokeDasharray={`${segment.length} ${circumference}`}
                    strokeDashoffset={segment.offset}
                    strokeLinecap="round"
                    transform={`rotate(-90 ${size / 2} ${size / 2})`}
                    style={{ transition: 'stroke-dashoffset 0.5s ease' }}
                  />
                ))
              ) : (
                // Если нет сегментов, показываем общий цвет
                <circle
                  cx={size / 2}
                  cy={size / 2}
                  r={radius}
                  fill="none"
                  stroke={chartColor}
                  strokeWidth="12"
                  strokeDasharray={strokeDasharray}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                  transform={`rotate(-90 ${size / 2} ${size / 2})`}
                  style={{ transition: 'stroke-dashoffset 0.5s ease' }}
                />
              )}
            </svg>
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Typography variant="h5" component="div" sx={{ fontWeight: 'bold', color: chartColor }}>
                {value.toFixed(1)}%
              </Typography>
            </Box>
          </Box>
          <Box sx={{ textAlign: 'center', width: '100%', mt: 1 }}>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
              {currentValue.toLocaleString()} / {maxValue.toLocaleString()} кг
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
              Свободно: {(maxValue - currentValue).toLocaleString()} кг
            </Typography>
          </Box>
        </Box>
        
        {/* Сводка товаров */}
        <Box sx={{ flex: 1, minWidth: 180 }}>
          {topItems.length === 0 ? (
            <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 2 }}>
              Товары отсутствуют
            </Typography>
          ) : (
            <>
              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, mb: 1, fontSize: '0.875rem' }}>
                Топ-{topItems.length} товаров:
              </Typography>
              <List dense sx={{ py: 0, maxHeight: size + 40, overflow: 'auto' }}>
                {topItems.map((item, index) => {
                  const percentage = totalWeight > 0 ? (item.weight / totalWeight * 100) : 0;
                  const itemColor = ITEM_COLORS[index % ITEM_COLORS.length];
                  return (
                    <ListItem key={item.id || index} sx={{ px: 0, py: 0.3 }}>
                      <Box
                        sx={{
                          width: 12,
                          height: 12,
                          borderRadius: '50%',
                          backgroundColor: itemColor,
                          mr: 1,
                          flexShrink: 0,
                          mt: 0.5,
                        }}
                      />
                      <ListItemText
                        primary={
                          <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                            <strong>{percentage.toFixed(1)}%</strong> - {item.sku_name}
                          </Typography>
                        }
                        secondary={
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
                            {item.weight.toLocaleString()} кг
                          </Typography>
                        }
                        sx={{ m: 0 }}
                      />
                    </ListItem>
                  );
                })}
              </List>
            </>
          )}
        </Box>
      </Box>
    </Paper>
  );
};

export default CircularProgressChart;

