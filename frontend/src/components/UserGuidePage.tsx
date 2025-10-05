import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  CircularProgress,
  Alert,
} from '@mui/material';
import ReactMarkdown from 'react-markdown';

/**
 * User Guide page component that dynamically loads and renders
 * markdown content from an external UserGuide.md file
 */
const UserGuidePage: React.FC = () => {
  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    /**
     * Fetch the UserGuide.md file from the public directory
     */
    const fetchUserGuide = async (): Promise<void> => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch the markdown file from the public directory
        const response = await fetch('/UserGuide.md');
        
        if (!response.ok) {
          throw new Error(`Failed to load user guide: ${response.status} ${response.statusText}`);
        }
        
        const markdownContent = await response.text();
        setContent(markdownContent);
      } catch (err) {
        console.error('Error loading user guide:', err);
        setError(err instanceof Error ? err.message : 'Failed to load user guide');
      } finally {
        setLoading(false);
      }
    };

    fetchUserGuide();
  }, []);

  if (loading) {
    return (
      <Box sx={{ p: 3, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress size={48} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading User Guide...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
          User Guide
        </Typography>
        <Alert severity="error" sx={{ mt: 2 }}>
          <Typography variant="h6" gutterBottom>
            Unable to load User Guide
          </Typography>
          <Typography variant="body2">
            {error}
          </Typography>
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
        User Guide
      </Typography>

      <Paper sx={{ p: 4 }}>
        <ReactMarkdown
          components={{
            h1: ({ children }) => (
              <Typography variant="h4" gutterBottom sx={{ mt: 3, mb: 2 }}>
                {children}
              </Typography>
            ),
            h2: ({ children }) => (
              <Typography variant="h5" gutterBottom sx={{ mt: 3, mb: 2 }}>
                {children}
              </Typography>
            ),
            h3: ({ children }) => (
              <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 1 }}>
                {children}
              </Typography>
            ),
            p: ({ children }) => (
              <Typography variant="body1" paragraph>
                {children}
              </Typography>
            ),
            ul: ({ children }) => (
              <Box component="ul" sx={{ pl: 3, mb: 2 }}>
                {children}
              </Box>
            ),
            ol: ({ children }) => (
              <Box component="ol" sx={{ pl: 3, mb: 2 }}>
                {children}
              </Box>
            ),
            li: ({ children }) => (
              <Typography component="li" variant="body1" sx={{ mb: 0.5 }}>
                {children}
              </Typography>
            ),
            code: ({ children }) => (
              <Box
                component="code"
                sx={{
                  bgcolor: 'grey.100',
                  px: 1,
                  py: 0.5,
                  borderRadius: 1,
                  fontFamily: 'monospace',
                  fontSize: '0.875rem'
                }}
              >
                {children}
              </Box>
            ),
            pre: ({ children }) => (
              <Box
                component="pre"
                sx={{
                  bgcolor: 'grey.100',
                  p: 2,
                  borderRadius: 1,
                  overflow: 'auto',
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                  mb: 2
                }}
              >
                {children}
              </Box>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </Paper>
    </Box>
  );
};

export default UserGuidePage;