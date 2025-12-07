import React from 'react';
import { Box, Typography, List, ListItem, ListItemText } from '@mui/material';
import { LocationTotal } from '../api/inventory';

interface LocationItemsListProps {
  items: LocationTotal[];
  totalWeight: number;
}

const LocationItemsList: React.FC<LocationItemsListProps> = ({ items, totalWeight }) => {
  // Сортируем по весу и берем топ-10
  const topItems = [...items]
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 10);

  if (topItems.length === 0) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary" align="center">
          Товары отсутствуют
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 1, maxHeight: 300, overflow: 'auto' }}>
      <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, mb: 1 }}>
        Топ-{topItems.length} товаров:
      </Typography>
      <List dense sx={{ py: 0 }}>
        {topItems.map((item, index) => {
          const percentage = totalWeight > 0 ? (item.weight / totalWeight * 100) : 0;
          return (
            <ListItem key={item.id || index} sx={{ px: 0, py: 0.5 }}>
              <ListItemText
                primary={
                  <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                    <strong>{percentage.toFixed(1)}%</strong> - {item.sku_name}
                  </Typography>
                }
                secondary={
                  <Typography variant="caption" color="text.secondary">
                    {item.weight.toLocaleString()} кг
                  </Typography>
                }
              />
            </ListItem>
          );
        })}
      </List>
    </Box>
  );
};

export default LocationItemsList;

