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
  Grid,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { fetchAuthSession } from 'aws-amplify/auth';
import axios from 'axios';
import useAdminRole from '../hooks/useAdminRole';
import ClearBucketsButton from './ClearBucketsButton';

const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const adminRole = useAdminRole();
  const [clearing, setClearing] = useState<boolean>(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [confirmOpen, setConfirmOpen] = useState<boolean>(false);

  const handleClearTables = async (): Promise<void> => {
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

  const handleClearSuccess = (): void => {
    setMessage({ type: 'success', text: 'Operation completed successfully' });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
        Settings
      </Typography>

      {/* Database & Storage Management - Admin Only */}
      {adminRole.isAdmin && (
        <Paper sx={{ p: 4, mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            Database & Storage Management
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Environment: <strong>{adminRole.environment.toUpperCase()}</strong>
          </Typography>
          
          {adminRole.environment === 'main' ? (
            <>
              <Typography variant="body1" color="text.secondary" gutterBottom>
                Destructive operations are disabled in production environment.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, my: 2 }}>
                <Button 
                  variant="contained" 
                  color="error"
                  disabled
                  sx={{ opacity: 0.5 }}
                >
                  Clear Tables (Disabled)
                </Button>
                <Button 
                  variant="contained" 
                  color="error"
                  disabled
                  sx={{ opacity: 0.5 }}
                >
                  Clear Buckets (Disabled)
                </Button>
              </Box>
              <Typography variant="caption" color="text.secondary">
                Clear operations are only available in DEV and TEST environments.
              </Typography>
            </>
          ) : (
            <>
              <Typography variant="body1" color="text.secondary" gutterBottom>
                Clear all data from the current environment's DynamoDB tables and S3 buckets.
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 2, my: 2 }}>
                <Button 
                  variant="contained" 
                  color="error"
                  onClick={() => setConfirmOpen(true)} 
                  disabled={clearing || !adminRole.canClearTables}
                >
                  {clearing ? <CircularProgress size={24} /> : 'Clear Tables'}
                </Button>
                
                <ClearBucketsButton 
                  disabled={!adminRole.canClearBuckets}
                  onSuccess={handleClearSuccess}
                />
              </Box>
              
              <Typography variant="caption" color="error">
                ⚠️ These actions cannot be undone!
              </Typography>
            </>
          )}

          {message && (
            <Alert severity={message.type} sx={{ mt: 2 }}>
              {message.text}
            </Alert>
          )}
        </Paper>
      )}

      {/* User Management - Admin Only */}
      {adminRole.isAdmin && (
        <Paper sx={{ p: 4, mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            User Management
          </Typography>
          <Typography variant="body1" color="text.secondary" gutterBottom>
            Manage user accounts and view system-wide data.
          </Typography>
          
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item>
              <Button 
                variant="outlined" 
                onClick={() => navigate('/admin/users')}
                disabled={!adminRole.canViewAllUsers}
              >
                View All Users
              </Button>
            </Grid>
            <Grid item>
              <Button 
                variant="outlined" 
                onClick={() => navigate('/admin/manage-users')}
                disabled={!adminRole.canManageUsers}
              >
                Manage Users
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* System Analytics - Admin Only */}
      {adminRole.isAdmin && (
        <Paper sx={{ p: 4, mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            System Analytics
          </Typography>
          <Typography variant="body1" color="text.secondary" gutterBottom>
            View system-wide statistics, logs, and performance metrics.
          </Typography>
          
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item>
              <Button 
                variant="outlined" 
                onClick={() => navigate('/admin/dashboard')}
                disabled={!adminRole.canViewSystemAnalytics}
              >
                System Dashboard
              </Button>
            </Grid>
            <Grid item>
              <Button 
                variant="outlined" 
                onClick={() => navigate('/admin/logs')}
                disabled={!adminRole.canViewSystemAnalytics}
              >
                View Logs
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Regular User Settings */}
      {!adminRole.isAdmin && (
        <Paper sx={{ p: 4 }}>
          <Typography variant="h5" color="textSecondary">
            User Settings
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mt: 2 }}>
            Additional user settings will be available here in future updates.
          </Typography>
        </Paper>
      )}

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