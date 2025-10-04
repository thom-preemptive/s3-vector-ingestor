import React from 'react';
import {
  Container,
  Typography,
  Paper,
} from '@mui/material';

const SettingsPage: React.FC = () => {
  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h5" color="textSecondary">
          Coming Soon
        </Typography>
      </Paper>
    </Container>
  );
};

export default SettingsPage;