import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Button,
  Chip,
  Divider,
  Grid,
  Card,
  CardContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Download as DownloadIcon,
  ExpandMore as ExpandMoreIcon,
  Description as DescriptionIcon,
  Storage as StorageIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import api from '../services/api';

interface DocumentData {
  document_id: string;
  filename: string;
  job_id: string;
  job_name: string;
  user_id: string;
  source_type: string;
  file_size: number;
  processed_at: string;
  markdown_s3_key: string;
  sidecar_s3_key: string;
  markdown_content?: string;
  sidecar_data?: any;
}

const DocumentViewerPage: React.FC = () => {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const [document, setDocument] = useState<DocumentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFullEmbeddings, setShowFullEmbeddings] = useState(false);

  useEffect(() => {
    if (documentId) {
      loadDocument();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentId]);

  const loadDocument = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDocument(documentId!);
      setDocument(data);
    } catch (err: any) {
      console.error('Failed to load document:', err);
      setError(err.message || 'Failed to load document');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (format: 'markdown' | 'json') => {
    if (!document) return;
    
    try {
      const blob = await api.downloadDocument(document.document_id, format);
      const url = window.URL.createObjectURL(blob);
      const link = window.document.createElement('a');
      link.href = url;
      link.download = `${document.filename}.${format === 'markdown' ? 'md' : 'json'}`;
      window.document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(url);
      window.document.body.removeChild(link);
    } catch (err: any) {
      console.error('Download failed:', err);
      setError(err.message || 'Download failed');
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error || !document) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error || 'Document not found'}
        </Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/documents')}>
          Back to Documents
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={() => navigate('/documents')}>
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h4">{document.filename}</Typography>
        </Box>
        <Box>
          <Tooltip title="Download Markdown">
            <IconButton color="primary" onClick={() => handleDownload('markdown')}>
              <DownloadIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Download JSON">
            <IconButton color="secondary" onClick={() => handleDownload('json')}>
              <StorageIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Metadata */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Document Information
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="textSecondary">
                  Job Name:
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {document.job_name}
                </Typography>

                <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                  Source Type:
                </Typography>
                <Chip
                  label={document.source_type.toUpperCase()}
                  color={document.source_type === 'pdf' ? 'error' : 'primary'}
                  size="small"
                  sx={{ mt: 0.5 }}
                />

                <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                  File Size:
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {formatBytes(document.file_size)}
                </Typography>

                <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                  Processed:
                </Typography>
                <Typography variant="body1">
                  {formatDate(document.processed_at)}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Storage Details
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="textSecondary">
                  Document ID:
                </Typography>
                <Typography variant="body2" fontFamily="monospace" gutterBottom>
                  {document.document_id}
                </Typography>

                <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                  Job ID:
                </Typography>
                <Typography variant="body2" fontFamily="monospace" gutterBottom>
                  {document.job_id}
                </Typography>

                <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                  Markdown S3 Key:
                </Typography>
                <Typography variant="body2" fontFamily="monospace" sx={{ wordBreak: 'break-all' }}>
                  {document.markdown_s3_key}
                </Typography>

                {document.sidecar_s3_key && (
                  <>
                    <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                      Sidecar S3 Key:
                    </Typography>
                    <Typography variant="body2" fontFamily="monospace" sx={{ wordBreak: 'break-all' }}>
                      {document.sidecar_s3_key}
                    </Typography>
                  </>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Markdown Content */}
      {document.markdown_content && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <DescriptionIcon sx={{ mr: 1 }} />
            <Typography variant="h6">Markdown Content</Typography>
          </Box>
          <Divider sx={{ mb: 2 }} />
          <Box
            sx={{
              '& h1': { fontSize: '2rem', fontWeight: 'bold', mt: 2, mb: 1 },
              '& h2': { fontSize: '1.5rem', fontWeight: 'bold', mt: 2, mb: 1 },
              '& h3': { fontSize: '1.25rem', fontWeight: 'bold', mt: 2, mb: 1 },
              '& p': { mb: 1 },
              '& code': { 
                backgroundColor: '#f5f5f5', 
                padding: '2px 6px', 
                borderRadius: '4px',
                fontFamily: 'monospace'
              },
              '& pre': {
                backgroundColor: '#f5f5f5',
                padding: '16px',
                borderRadius: '8px',
                overflow: 'auto',
                '& code': {
                  backgroundColor: 'transparent',
                  padding: 0
                }
              },
              '& ul, & ol': { pl: 4 },
            }}
          >
            <ReactMarkdown>{document.markdown_content}</ReactMarkdown>
          </Box>
        </Paper>
      )}

      {/* Sidecar Data */}
      {document.sidecar_data && (
        <Accordion sx={{ mb: 3 }}>
          <AccordionSummary 
            expandIcon={<ExpandMoreIcon />}
            aria-controls="sidecar-content"
            id="sidecar-header"
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
              <StorageIcon sx={{ color: 'primary.main' }} />
              <Box sx={{ flex: 1 }}>
                <Typography variant="h6">Vector Sidecar Data</Typography>
                <Typography variant="caption" color="textSecondary">
                  {document.sidecar_data.total_chunks || 0} chunks • 
                  {document.sidecar_data.embedding_model || 'Unknown model'} • 
                  {document.sidecar_data.quality_metrics?.success_rate || 0}% success rate
                </Typography>
              </Box>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ p: 2 }}>
              {/* Summary Statistics */}
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                        Embedding Information
                      </Typography>
                      <Typography variant="body2">
                        <strong>Model:</strong> {document.sidecar_data.embedding_model}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Dimensions:</strong> {document.sidecar_data.embedding_dimensions}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Created:</strong> {formatDate(document.sidecar_data.created_at)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                        Processing Results
                      </Typography>
                      <Typography variant="body2">
                        <strong>Total Chunks:</strong> {document.sidecar_data.total_chunks}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Successful:</strong> {document.sidecar_data.successful_chunks}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Failed:</strong> {document.sidecar_data.failed_chunks}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                {document.sidecar_data.chunking_strategy && (
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                          Chunking Strategy
                        </Typography>
                        <Typography variant="body2">
                          <strong>Chunk Size:</strong> {document.sidecar_data.chunking_strategy.chunk_size} words
                        </Typography>
                        <Typography variant="body2">
                          <strong>Overlap:</strong> {document.sidecar_data.chunking_strategy.overlap_size} words
                        </Typography>
                        <Typography variant="body2">
                          <strong>Dynamic Sizing:</strong> {document.sidecar_data.chunking_strategy.dynamic_sizing ? 'Yes' : 'No'}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                )}

                {document.sidecar_data.processing_statistics && (
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                          Processing Statistics
                        </Typography>
                        <Typography variant="body2">
                          <strong>Original Words:</strong> {document.sidecar_data.processing_statistics.original_word_count?.toLocaleString()}
                        </Typography>
                        <Typography variant="body2">
                          <strong>Avg Chunk Size:</strong> {document.sidecar_data.processing_statistics.average_chunk_size_words} words
                        </Typography>
                        <Typography variant="body2">
                          <strong>Processing Time:</strong> {document.sidecar_data.processing_statistics.total_embedding_time_seconds}s
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                )}

                {document.sidecar_data.quality_metrics && (
                  <Grid item xs={12}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                          Quality Metrics
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 4 }}>
                          <Box>
                            <Typography variant="body2">
                              <strong>Success Rate:</strong> {document.sidecar_data.quality_metrics.success_rate}%
                            </Typography>
                          </Box>
                          <Box>
                            <Typography variant="body2">
                              <strong>Chunk Utilization:</strong> {document.sidecar_data.quality_metrics.chunk_utilization}%
                            </Typography>
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                )}
              </Grid>

              {/* Chunk Preview */}
              {document.sidecar_data.chunks && document.sidecar_data.chunks.length > 0 && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Chunk Preview (First 3 chunks)
                  </Typography>
                  {document.sidecar_data.chunks.slice(0, 3).map((chunk: any, index: number) => (
                    <Card key={index} variant="outlined" sx={{ mb: 2 }}>
                      <CardContent>
                        <Typography variant="subtitle2" color="primary" gutterBottom>
                          Chunk {chunk.chunk_index} - ID: {chunk.chunk_id}
                        </Typography>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          <strong>Text Preview:</strong> {chunk.text?.substring(0, 200)}...
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          <strong>Words:</strong> {chunk.metadata?.word_count} • 
                          <strong> Tokens:</strong> {chunk.metadata?.estimated_tokens} • 
                          <strong> Embedding Dimensions:</strong> {chunk.embedding?.length || 0}
                        </Typography>
                      </CardContent>
                    </Card>
                  ))}
                  {document.sidecar_data.chunks.length > 3 && (
                    <Alert severity="info" sx={{ mb: 2 }}>
                      Showing 3 of {document.sidecar_data.chunks.length} chunks. 
                      Full embeddings contain {document.sidecar_data.chunks.length} chunks with {document.sidecar_data.embedding_dimensions}-dimensional vectors.
                    </Alert>
                  )}
                </>
              )}

              {/* Full JSON Export Option */}
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <Button
                  variant="outlined"
                  onClick={() => setShowFullEmbeddings(!showFullEmbeddings)}
                  startIcon={showFullEmbeddings ? <ExpandMoreIcon sx={{ transform: 'rotate(180deg)' }} /> : <ExpandMoreIcon />}
                >
                  {showFullEmbeddings ? 'Hide' : 'Show'} Full JSON (Warning: Large)
                </Button>
                <Button
                  variant="contained"
                  onClick={() => handleDownload('json')}
                  startIcon={<DownloadIcon />}
                >
                  Download Full Sidecar JSON
                </Button>
              </Box>

              {/* Full JSON Display (Hidden by default) */}
              {showFullEmbeddings && (
                <Paper
                  elevation={0}
                  sx={{
                    mt: 2,
                    p: 2,
                    backgroundColor: '#f5f5f5',
                    maxHeight: '600px',
                    overflow: 'auto',
                    border: '1px solid #e0e0e0',
                  }}
                >
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    This displays {document.sidecar_data.chunks?.length || 0} chunks with full {document.sidecar_data.embedding_dimensions}-dimensional vectors. 
                    This may slow down your browser.
                  </Alert>
                  <pre style={{ 
                    margin: 0, 
                    whiteSpace: 'pre-wrap', 
                    wordBreak: 'break-word',
                    fontSize: '11px',
                    fontFamily: 'Monaco, Consolas, "Courier New", monospace'
                  }}>
                    {JSON.stringify(document.sidecar_data, null, 2)}
                  </pre>
                </Paper>
              )}
            </Box>
          </AccordionDetails>
        </Accordion>
      )}
    </Container>
  );
};

export default DocumentViewerPage;
