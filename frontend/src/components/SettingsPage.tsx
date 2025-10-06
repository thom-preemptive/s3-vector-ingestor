import React, { useState, useEffect } from 'react';
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
  TextField,
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
  const [pdfMessage, setPdfMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [confirmOpen, setConfirmOpen] = useState<boolean>(false);
  
  // PDF OCR Settings
  const [ocrThreshold, setOcrThreshold] = useState<number>(200);
  const [loadingSettings, setLoadingSettings] = useState<boolean>(true);
  const [savingSettings, setSavingSettings] = useState<boolean>(false);

  // Load settings on component mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async (): Promise<void> => {
    setLoadingSettings(true);
    try {
      const API_URL = process.env.REACT_APP_API_URL;
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();

      if (!token) {
        console.warn('Not authenticated, using default settings');
        setLoadingSettings(false);
        return;
      }

      const response = await axios.get(
        `${API_URL}/settings/ocr-threshold`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.data.threshold) {
        setOcrThreshold(response.data.threshold);
      }
    } catch (error) {
      console.warn('Failed to load settings, using defaults:', error);
      // Keep default value of 200
    } finally {
      setLoadingSettings(false);
    }
  };

  const saveSettings = async (): Promise<void> => {
    setSavingSettings(true);
    setPdfMessage(null);

    try {
      const API_URL = process.env.REACT_APP_API_URL;
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();

      if (!token) {
        setPdfMessage({ type: 'error', text: 'Not authenticated' });
        setSavingSettings(false);
        return;
      }

      await axios.post(
        `${API_URL}/settings/ocr-threshold`,
        { threshold: ocrThreshold },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setPdfMessage({ type: 'success', text: 'Settings saved successfully' });
    } catch (err) {
      const error = err as any; // Type assertion for error handling
      console.error('Failed to save settings:', error);
      
      // Enhanced error logging for debugging
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response data:', error.response.data);
        
        if (error.response.status === 401) {
          setPdfMessage({ type: 'error', text: 'Authentication failed. Please refresh the page and try again.' });
        } else if (error.response.status === 403) {
          setPdfMessage({ type: 'error', text: 'Access denied. You may not have permission to modify settings.' });
        } else {
          setPdfMessage({ type: 'error', text: `Failed to save settings: ${error.response.data?.detail || error.message}` });
        }
      } else if (error.request) {
        console.error('No response received:', error.request);
        setPdfMessage({ type: 'error', text: 'No response from server. Please check your connection.' });
      } else {
        console.error('Error setting up request:', error.message);
        setPdfMessage({ type: 'error', text: `Failed to save settings: ${error.message}` });
      }
    } finally {
      setSavingSettings(false);
    }
  };

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

      {/* PDF Ingestion Settings */}
      <Paper sx={{ p: 2, mb: 1.5 }}>
        <Typography variant="h5" gutterBottom>
          PDF Ingestion
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Configure how PDF documents are processed for text extraction and OCR.
        </Typography>
        
        {loadingSettings ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <CircularProgress size={20} />
            <Typography variant="body2">Loading settings...</Typography>
          </Box>
        ) : (
          <>
            <Grid container spacing={3} alignItems="center">
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  label="OCR Word Count Threshold"
                  type="number"
                  value={ocrThreshold}
                  onChange={(e) => setOcrThreshold(Math.max(1, Math.min(10000, parseInt(e.target.value) || 200)))}
                  inputProps={{ min: 1, max: 10000 }}
                  fullWidth
                  helperText="PDFs with fewer words will use OCR processing (1-10,000)"
                />
              </Grid>
              <Grid item xs={12} sm={6} md={8}>
                <Typography variant="body2" color="text.secondary">
                  When a PDF contains fewer than this number of words, AWS Textract OCR will be used for text extraction. 
                  Higher values may improve accuracy for image-heavy PDFs but will increase processing costs.
                </Typography>
              </Grid>
            </Grid>
            
            <Box sx={{ mt: 3 }}>
              <Button
                variant="contained"
                onClick={saveSettings}
                disabled={savingSettings}
                sx={{ mr: 2 }}
              >
                {savingSettings ? <CircularProgress size={24} /> : 'Save Settings'}
              </Button>
              <Button
                variant="outlined"
                onClick={loadSettings}
                disabled={loadingSettings || savingSettings}
              >
                Reset to Saved
              </Button>
            </Box>

            {/* PDF Settings Message */}
            {pdfMessage && (
              <Alert severity={pdfMessage.type} sx={{ mt: 2 }}>
                {pdfMessage.text}
              </Alert>
            )}
          </>
        )}
      </Paper>

      {/* Database & Storage Management - Admin Only */}
      {adminRole.isAdmin && (
        <Paper sx={{ p: 2, mb: 1.5 }}>
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
        <Paper sx={{ p: 2, mb: 1.5 }}>
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
        <Paper sx={{ p: 2, mb: 1.5 }}>
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
        <Paper sx={{ p: 2 }}>
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