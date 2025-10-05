import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material';
import { fetchAuthSession } from 'aws-amplify/auth';
import axios from 'axios';

const SettingsPage: React.FC = () => {
  const [clearing, setClearing] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const handleClearTables = async () => {
    setConfirmOpen(false);
    setClearing(true);
    setMessage(null);

    try {
      const API_URL = process.env.REACT_APP_API_URL;
      
      // Get authentication token
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();

      if (!token) {
        setMessage({ type: 'error', text: 'Not authenticated' });
        setClearing(false);
        return;
      }

      const response = await axios.post(
        `${API_URL}/admin/clear-tables`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setMessage({ 
        type: 'success', 
        text: response.data.message || 'Tables cleared successfully' 
      });
    } catch (error: any) {
      console.error('Error clearing tables:', error);
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to clear tables' 
      });
    } finally {
      setClearing(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Paper sx={{ p: 4 }}>
        <Typography variant="h5" gutterBottom>
          Database Management
        </Typography>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Clear all data from the current environment's DynamoDB tables (jobs, approvals, user tracking).
        </Typography>

        <Button 
          variant="contained" 
          color="error"
          onClick={() => setConfirmOpen(true)} 
          disabled={clearing}
          sx={{ my: 2 }}
        >
          {clearing ? <CircularProgress size={24} /> : 'Clear Tables'}
        </Button>

        {message && (
          <Alert severity={message.type} sx={{ mt: 2 }}>
            {message.text}
          </Alert>
        )}
      </Paper>

      {/* Confirmation Dialog */}
      <Dialog
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
      >
        <DialogTitle>Confirm Clear Tables</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to clear all tables in this environment? This will delete:
            <ul>
              <li>All job records</li>
              <li>All approval requests</li>
              <li>All user tracking data</li>
            </ul>
            <strong>This action cannot be undone!</strong>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmOpen(false)} color="primary">
            Cancel
          </Button>
          <Button onClick={handleClearTables} color="error" variant="contained">
            Clear Tables
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SettingsPage;