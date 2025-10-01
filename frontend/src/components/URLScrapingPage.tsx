import React from 'react';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  FormControlLabel,
  Switch,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Language as UrlIcon } from '@mui/icons-material';

interface URLScrapingPageProps {
  user?: any;
}

const URLScrapingPage: React.FC<URLScrapingPageProps> = ({ user }) => {
  const [urls, setUrls] = React.useState<string>('');
  const [jobName, setJobName] = React.useState<string>('');
  const [notes, setNotes] = React.useState<string>('');
  const [approvalRequired, setApprovalRequired] = React.useState<boolean>(true);
  const [processing, setProcessing] = React.useState<boolean>(false);
  const [processResult, setProcessResult] = React.useState<any>(null);
  const [error, setError] = React.useState<string>('');

  // Check if current user is thom@preemptive.tech to hide approval option
  const userEmail = user?.signInDetails?.loginId || user?.attributes?.email || user?.username || '';
  const isThomUser = userEmail === 'thom@preemptive.tech';

  // Set default approval state based on user
  React.useEffect(() => {
    if (isThomUser) {
      setApprovalRequired(false);
    }
  }, [isThomUser]);

  const handleSubmit = async () => {
    if (!urls.trim()) {
      setError('Please enter at least one URL');
      return;
    }

    if (!jobName.trim()) {
      setError('Please enter a job name');
      return;
    }

    setProcessing(true);
    setError('');
    setProcessResult(null);

    try {
      const urlList = urls.split('\n').filter(url => url.trim());
      
      // Check if we have a backend API configured
      const apiUrl = process.env.REACT_APP_API_URL || '';
      if (!apiUrl) {
        throw new Error('Backend API not yet deployed. This is a frontend-only demo. Backend deployment coming soon!');
      }
      
      const response = await fetch(`${apiUrl}/api/process/urls`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          urls: urlList,
          user_id: 'current-user', // TODO: Get from auth context
          job_name: jobName,
          notes: notes,
          approval_required: approvalRequired,
        }),
      });

      if (!response.ok) {
        throw new Error('URL processing failed');
      }

      const result = await response.json();
      setProcessResult(result);

      // Clear form on success
      setUrls('');
      setJobName('');
      setNotes('');
    } catch (err: any) {
      if (err.message.includes('Failed to fetch') || err.name === 'TypeError') {
        setError('Backend API not available. This is a frontend-only demo. Backend deployment coming soon!');
      } else {
        setError(err.message || 'An error occurred');
      }
    } finally {
      setProcessing(false);
    }
  };

  const urlCount = urls.split('\n').filter(url => url.trim()).length;

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        URL Scraping
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Extract content from web pages and convert them to markdown format for processing.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {processResult && (
        <Alert severity="success" sx={{ mb: 2 }}>
          URL processing job submitted successfully! Job ID: {processResult.job_id}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Job Title
        </Typography>
        <TextField
          fullWidth
          label="Job Title"
          value={jobName}
          onChange={(e) => setJobName(e.target.value)}
          sx={{ mb: 2 }}
          placeholder="e.g., Website Content Scraping - Q4 2024"
        />
        <Box sx={{ mb: 2 }}>
          <Typography variant="body1" sx={{ mb: 1, fontWeight: 500 }}>
            Notes
          </Typography>
          <ReactQuill
            theme="snow"
            value={notes}
            onChange={setNotes}
            placeholder="Optional details about information source, et cetera"
            style={{ 
              height: '100px',
              marginBottom: '50px' // Extra space for toolbar
            }}
            modules={{
              toolbar: [
                [{ 'header': [1, 2, false] }],
                ['bold', 'italic', 'underline'],
                ['link'],
                [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                ['clean']
              ],
            }}
          />
        </Box>
        {!isThomUser && (
          <FormControlLabel
            control={
              <Switch
                checked={approvalRequired}
                onChange={(e) => setApprovalRequired(e.target.checked)}
              />
            }
            label="Require approval before processing"
          />
        )}
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          URLs to Process
        </Typography>
        <TextField
          fullWidth
          multiline
          rows={8}
          label="URLs"
          value={urls}
          onChange={(e) => setUrls(e.target.value)}
          placeholder="Enter URLs, one per line&#10;&#10;Example:&#10;https://example.com/page1&#10;https://example.com/page2&#10;https://docs.example.com/guide"
          helperText={`Enter one URL per line. These will be scraped and processed into markdown format. ${urlCount > 0 ? `(${urlCount} URL${urlCount !== 1 ? 's' : ''} entered)` : ''}`}
          sx={{
            '& .MuiInputBase-input': {
              fontFamily: 'monospace',
              fontSize: '0.9rem',
            }
          }}
        />
      </Paper>

      <Paper sx={{ p: 3, mb: 3, backgroundColor: '#EFE6F7', color: 'black' }}>
        <Typography variant="h6" gutterBottom sx={{ color: 'black' }}>
          How URL Scraping Works
        </Typography>
        <Typography variant="body2" component="div" sx={{ color: 'black' }}>
          <Box component="ul" sx={{ pl: 2, mb: 0 }}>
            <li>Each URL will be visited and its content extracted</li>
            <li>Web page content is converted to clean markdown format</li>
            <li>Text is processed and vectorized for search capabilities</li>
            <li>Results are stored with the job name you specify</li>
            <li>Processing may take several minutes depending on content size</li>
          </Box>
        </Typography>
      </Paper>

      <Box sx={{ textAlign: 'center' }}>
        <Button
          variant="contained"
          size="large"
          onClick={handleSubmit}
          disabled={processing || !urls.trim() || !jobName.trim()}
          startIcon={processing ? <CircularProgress size={20} /> : <UrlIcon />}
          sx={{
            backgroundColor: '#6a37b0',
            '&:hover': {
              backgroundColor: '#5a2e9a',
            },
          }}
        >
          {processing ? 'Processing URLs...' : `Process ${urlCount > 0 ? urlCount : ''} URL${urlCount !== 1 ? 's' : ''}`}
        </Button>
      </Box>
    </Box>
  );
};

export default URLScrapingPage;