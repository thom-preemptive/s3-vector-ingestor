import React, { useState } from 'react';
import {
  Button,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Typography,
  Box,
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import { fetchAuthSession } from 'aws-amplify/auth';
import axios from 'axios';

interface ClearBucketsButtonProps {
  disabled?: boolean;
  onSuccess?: () => void;
}

/**
 * Admin component for clearing S3 bucket contents
 * Only available in DEV and TEST environments
 */
const ClearBucketsButton: React.FC<ClearBucketsButtonProps> = ({ 
  disabled = false, 
  onSuccess 
}) => {
  const [clearing, setClearing] = useState<boolean>(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [confirmOpen, setConfirmOpen] = useState<boolean>(false);
  const [understood, setUnderstood] = useState<boolean>(false);
  const [confirmed, setConfirmed] = useState<boolean>(false);

  const environment = process.env.REACT_APP_ENVIRONMENT || 'unknown';

  const handleClearBuckets = async (): Promise<void> => {
    setConfirmOpen(false);
    setClearing(true);
    setMessage(null);
    setUnderstood(false);
    setConfirmed(false);

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
        `${API_URL}/admin/clear-buckets`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setMessage({ 
        type: 'success', 
        text: response.data.message || 'S3 buckets cleared successfully' 
      });

      if (onSuccess) {
        onSuccess();
      }
    } catch (error: any) {
      console.error('Error clearing buckets:', error);
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to clear buckets' 
      });
    } finally {
      setClearing(false);
    }
  };

  const canConfirm = understood && confirmed;

  return (
    <>
      <Button 
        variant="contained" 
        color="error"
        onClick={() => setConfirmOpen(true)} 
        disabled={clearing || disabled}
        sx={{ ml: 2 }}
      >
        {clearing ? <CircularProgress size={24} /> : 'Clear Buckets'}
      </Button>

      {message && (
        <Alert severity={message.type} sx={{ mt: 2 }}>
          {message.text}
        </Alert>
      )}

      {/* Confirmation Dialog */}
      <Dialog
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          ⚠️ Confirm Clear Buckets - {environment.toUpperCase()} Environment
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            This will permanently delete all S3 bucket contents:
          </DialogContentText>
          
          <Box sx={{ mt: 2, mb: 2 }}>
            <Typography variant="body2" component="ul" sx={{ pl: 2 }}>
              <li>All processed documents (.md files)</li>
              <li>All vector sidecars (.json files)</li>
              <li>All uploaded files (.pdf files)</li>
              <li>Document manifest (manifest.json)</li>
            </Typography>
          </Box>

          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            <strong>Environment:</strong> {environment.toUpperCase()}
          </Typography>

          <Box sx={{ mt: 3 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={understood}
                  onChange={(e) => setUnderstood(e.target.checked)}
                  color="error"
                />
              }
              label="I understand this cannot be undone"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.target.checked)}
                  color="error"
                />
              }
              label="I confirm I want to clear all bucket contents"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmOpen(false)} color="primary">
            Cancel
          </Button>
          <Button 
            onClick={handleClearBuckets} 
            color="error" 
            variant="contained"
            disabled={!canConfirm}
          >
            Clear Buckets
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ClearBucketsButton;