import React from 'react';
import {
  Box,
  Typography,
  Paper,
} from '@mui/material';

const SettingsPage: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Paper sx={{ p: 4 }}>
        <Typography variant="h5" color="textSecondary">
          Coming Soon
        </Typography>
      </Paper>
    </Box>
  );
};

export default SettingsPage;