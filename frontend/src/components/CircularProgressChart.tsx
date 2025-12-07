import React from 'react';
import { Box, Typography, Paper, List, ListItem, ListItemText } from '@mui/material';
import { LocationTotal } from '../api/inventory';

interface CircularProgressChartProps {
  value: number; // Процент заполнения (0-100)
  maxValue: number; // Максимальное значение
  currentValue: number; // Текущее значение (в кг)
  label: string;
  size?: number;
  color?: string;
  items?: LocationTotal[]; // Товары для отображения
}

const ITEM_COLORS = [
  '#1976d2', '#9c27b0', '#ed6c02', '#2e7d32', '#d32f2f',
  '#0288d1', '#7b1fa2', '#f57c00', '#388e3c', '#c62828',
  '#0277bd', '#6a1b9a', '#ef6c00', '#2e7d32', '#b71c1c',
];

const toRadians = (deg: number) => (deg * Math.PI) / 180;

/**
 * Возвращает SVG path для дуги от startAngle до endAngle (в градусах).
 * Центр (cx, cy), радиус r.
 * Угол 0 соответствует правой точке, поэтому мы поворачиваем всю группу на -90deg внешне.
 */
function describeArc(cx: number, cy: number, r: number, startAngle: number, endAngle: number) {
  const start = {
    x: cx + r * Math.cos(toRadians(startAngle)),
    y: cy + r * Math.sin(toRadians(startAngle)),
  };
  const end = {
    x: cx + r * Math.cos(toRadians(endAngle)),
    y: cy + r * Math.sin(toRadians(endAngle)),
  };
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArcFlag} 1 ${end.x} ${end.y}`;
}

const CircularProgressChart: React.FC<CircularProgressChartProps> = ({
  value,
  maxValue,
  currentValue,
  label,
  size = 120,
  color = '#1976d2',
  items = [],
}) => {
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const cx = size / 2;
  const cy = size / 2;

  // Цвет в зависимости от заполнения (оставил вашу логику)
  let chartColor = color;
  if (value >= 90) {
    chartColor = '#d32f2f';
  } else if (value >= 75) {
    chartColor = '#ed6c02';
  } else if (value >= 50) {
    chartColor = '#ed6c02';
  } else {
    chartColor = '#2e7d32';
  }

  // Топ товаров
  const topItems = [...items].sort((a, b) => b.weight - a.weight).slice(0, 10);
  const totalItemsWeight = topItems.reduce((s, it) => s + (it.weight || 0), 0);
  const safeTotalItemsWeight = totalItemsWeight > 0 ? totalItemsWeight : 1;
  const safeCurrentValue = currentValue > 0 ? currentValue : safeTotalItemsWeight;

  // Полный угол заполненной части (в градусах)
  const filledAngle = Math.max(0, Math.min(100, value)) / 100 * 360;

  // epsilon — небольшой перекрывающийся угол (в градусах) чтобы убрать щели из-за округлений/антиалиасинга
  const EPSILON_DEG = 0.25;

  type Segment = { color: string; startAngle: number; endAngle: number; percentage: number };
  const segments: Segment[] = [];

  if (topItems.length > 0 && filledAngle > 0 && safeTotalItemsWeight > 0) {
    let accAngle = 0; // начальный угол внутри заполненной части, 0..filledAngle

    topItems.forEach((item, idx) => {
      const w = item.weight || 0;
      // угол сегмента пропорционален весу
      const angleForItem = (w / safeTotalItemsWeight) * filledAngle;
      const start = accAngle;
      const end = accAngle + angleForItem;

      // Если слишком маленький угол — игнорируем (не рисуем)
      if (angleForItem > 0.2) {
        segments.push({
          color: ITEM_COLORS[idx % ITEM_COLORS.length],
          // Переводим в стандартные svg-углы: 0deg — правая точка, идём против часовой (но мы будем поворачивать группу на -90)
          // Чтобы начало заполненной части было сверху, сдвинем на -90deg при рендере всей группы.
          startAngle: start,
          endAngle: end,
          percentage: safeCurrentValue > 0 ? (w / safeCurrentValue) * 100 : 0,
        });
      }
      accAngle += angleForItem;
    });
  }

  // Функция для получения итогового path с применением поворота старта (чтобы 0 градусов был сверху)
  const renderSegments = () => {
    // Начало заполненной части должно располагаться в верхней позиции: это будет offsetStart = -filledAngle/2 ? Нет — мы хотим начать с верхней точки и идти по часовой.
    // Наш describeArc считает угол от 0 (справа) и поворачивает по стандартному направлению (по часовой — используется sweep-flag=1).
    // Чтобы начинать сверху, добавим -90deg к каждому углу и сдвинем от начала заполненной части:
    const startOfFilledGlobal = -90; // верхняя точка в градусах
    const segmentsPaths = segments.map((seg, idx) => {
      // Углы сегмента в глобальной системе: startOfFilledGlobal + seg.startAngle .. + seg.endAngle
      let s = startOfFilledGlobal + seg.startAngle;
      let e = startOfFilledGlobal + seg.endAngle;

      // Добавим небольшой перекрывающийся буфер:
      if (idx !== 0) s -= EPSILON_DEG;
      if (idx !== segments.length - 1) e += EPSILON_DEG;

      // describeArc ожидает startAngle < endAngle (если end < start — largeArcFlag и sweep могут сломаться), но у нас это так
      // Если по округлениям e превысит s сильно — fine.
      const path = describeArc(cx, cy, radius, s, e);
      return (
        <path
          key={idx}
          d={path}
          fill="none"
          stroke={seg.color}
          strokeWidth={strokeWidth}
          strokeLinecap="butt"
          strokeLinejoin="miter"
        />
      );
    });

    return segmentsPaths;
  };

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
              {/* фон */}
              <circle cx={cx} cy={cy} r={radius} fill="none" stroke="#e0e0e0" strokeWidth={strokeWidth} />
              {/* рисуем заполненную часть как набор дуг.
                  Замечание: describeArc рисует дуги по часовой (sweep-flag=1) от startAngle к endAngle. 
                  Мы передаём start/end как глобальные градусы (сдвинутые на -90deg), поэтому дуги начнутся сверху. */}
              <g>
                {renderSegments()}
              </g>
              {/* Если нет сегментов — рисуем единый цветной круг по заполненной части */}
              {segments.length === 0 && value > 0 && (
                <path
                  d={describeArc(cx, cy, radius, -90, -90 + filledAngle)}
                  fill="none"
                  stroke={chartColor}
                  strokeWidth={strokeWidth}
                  strokeLinecap="butt"
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

        <Box sx={{ flex: 1, minWidth: 180 }}>
          {topItems.length === 0 ? (
            <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 2 }}>
              Товары отсутствуют
            </Typography>
          ) : (
            <>
              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, mb: 1, fontSize: '1.2rem' }}>
                Топ-{topItems.length} товаров:
              </Typography>
              <List dense sx={{ py: 0, maxHeight: size + 40, overflow: 'auto' }}>
                {topItems.map((item, index) => {
                  const percentage = safeCurrentValue > 0 ? (item.weight / safeCurrentValue) * 100 : 0;
                  const itemColor = ITEM_COLORS[index % ITEM_COLORS.length];
                  return (
                    <ListItem key={item.id || index} sx={{ px: 0, py: 0.3 }}>
                      <Box
                        sx={{
                          width: 15,
                          height: 15,
                          borderRadius: '100%',
                          backgroundColor: itemColor,
                          mr: 1,
                          flexShrink: 0,
                          mt: 0.5,
                        }}
                      />
                      <ListItemText
                        primary={
                          <Typography variant="body2" sx={{ fontSize: '1rem' }}>
                            <strong>{percentage.toFixed(1)}%</strong> - {item.sku_name}
                          </Typography>
                        }
                        secondary={
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
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
