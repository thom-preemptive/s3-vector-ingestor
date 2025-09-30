import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Paper,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  TextField,
  FormControlLabel,
  Switch,
  Alert,
  CircularProgress,
} from '@mui/material';
import { CloudUpload as UploadIcon } from '@mui/icons-material';

interface UploadPageProps {}

const UploadPage: React.FC<UploadPageProps> = () => {
  const [files, setFiles] = React.useState<File[]>([]);
  const [jobName, setJobName] = React.useState<string>('');
  const [approvalRequired, setApprovalRequired] = React.useState<boolean>(true);
  const [uploading, setUploading] = React.useState<boolean>(false);
  const [uploadResult, setUploadResult] = React.useState<any>(null);
  const [error, setError] = React.useState<string>('');

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles(prev => [...prev, ...acceptedFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: true
  });

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (files.length === 0) {
      setError('Please select at least one PDF file');
      return;
    }
    if (!jobName.trim()) {
      setError('Please enter a job name');
      return;
    }

    setUploading(true);
    setError('');
    setUploadResult(null);

    try {
      const formData = new FormData();
      files.forEach(file => formData.append('files', file));
      formData.append('job_name', jobName);
      formData.append('approval_required', approvalRequired.toString());

      const response = await fetch('/api/upload/pdf', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const result = await response.json();
      setUploadResult(result);

      // Clear form on success
      setFiles([]);
      setJobName('');
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        Upload Documents
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Upload PDF documents for processing and vectorization. Files will be converted to markdown and made searchable.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {uploadResult && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Job submitted successfully! Job ID: {uploadResult.job_id}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Job Details
        </Typography>
        <TextField
          fullWidth
          label="Job Name"
          value={jobName}
          onChange={(e) => setJobName(e.target.value)}
          sx={{ mb: 2 }}
          placeholder="e.g., Emergency Response Documents - Q4 2024"
        />
        <FormControlLabel
          control={
            <Switch
              checked={approvalRequired}
              onChange={(e) => setApprovalRequired(e.target.checked)}
            />
          }
          label="Require approval before processing"
        />
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Upload PDF Files
        </Typography>
        <Box
          {...getRootProps()}
          sx={{
            border: '2px dashed',
            borderColor: isDragActive ? 'primary.main' : 'grey.300',
            borderRadius: 1,
            p: 3,
            textAlign: 'center',
            cursor: 'pointer',
            backgroundColor: isDragActive ? 'action.hover' : 'transparent',
            mb: 2,
          }}
        >
          <input {...getInputProps()} />
          <UploadIcon sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
          <Typography variant="body1" gutterBottom>
            {isDragActive
              ? 'Drop the PDF files here...'
              : 'Drag & drop PDF files here, or click to select'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Only PDF files are supported
          </Typography>
        </Box>

        {files.length > 0 && (
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Selected Files ({files.length})
            </Typography>
            <List dense>
              {files.map((file, index) => (
                <ListItem
                  key={index}
                  secondaryAction={
                    <Button
                      size="small"
                      color="error"
                      onClick={() => removeFile(index)}
                    >
                      Remove
                    </Button>
                  }
                >
                  <ListItemText
                    primary={file.name}
                    secondary={`${(file.size / 1024 / 1024).toFixed(2)} MB`}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </Paper>

      <Box sx={{ textAlign: 'center' }}>
        <Button
          variant="contained"
          size="large"
          onClick={handleSubmit}
          disabled={uploading || files.length === 0 || !jobName.trim()}
          startIcon={uploading ? <CircularProgress size={20} /> : <UploadIcon />}
        >
          {uploading ? 'Uploading...' : 'Upload Documents'}
        </Button>
      </Box>
    </Box>
  );
};

export default UploadPage;