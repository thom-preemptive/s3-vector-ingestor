import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  TextField,
  InputAdornment,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Button,
  CircularProgress,
  Alert,
  Pagination,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import {
  Search as SearchIcon,
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
  Description as DescriptionIcon,
  PictureAsPdf as PdfIcon,
  Language as LanguageIcon,
} from '@mui/icons-material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../services/api';

interface Document {
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
  match_field?: string;
}

interface DocumentStats {
  total_documents: number;
  pdf_documents: number;
  url_documents: number;
  total_size_bytes: number;
  latest_upload: string;
  unique_users: number;
  unique_jobs: number;
}

const DocumentsPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [stats, setStats] = useState<DocumentStats | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const docsPerPage = 20;

  useEffect(() => {
    loadDocuments();
    loadStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, searchParams]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      const offset = (page - 1) * docsPerPage;
      const data = await api.listDocuments(docsPerPage, offset);
      
      // Filter by job if job parameter is present
      const jobFilter = searchParams.get('job');
      let filteredDocuments = data.documents;
      if (jobFilter) {
        filteredDocuments = data.documents.filter((doc: Document) => doc.job_id === jobFilter);
      }
      
      setDocuments(filteredDocuments);
      setTotalPages(Math.ceil(filteredDocuments.length / docsPerPage));
    } catch (err: any) {
      console.error('Failed to load documents:', err);
      setError(err.message || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const statsData = await api.getDocumentStats();
      setStats(statsData);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery || searchQuery.length < 2) {
      loadDocuments();
      return;
    }

    try {
      setSearching(true);
      setError(null);
      const data = await api.searchDocuments(searchQuery);
      setDocuments(data.results);
      setTotalPages(1); // Search results on single page
    } catch (err: any) {
      console.error('Search failed:', err);
      setError(err.message || 'Search failed');
    } finally {
      setSearching(false);
    }
  };

  const handleViewDocument = (documentId: string) => {
    navigate(`/documents/${documentId}`);
  };

  const handleDownload = async (documentId: string, filename: string, format: 'markdown' | 'json') => {
    try {
      const blob = await api.downloadDocument(documentId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.${format === 'markdown' ? 'md' : 'json'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
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

  const getSourceIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'pdf':
        return <PdfIcon color="error" />;
      case 'url':
        return <LanguageIcon color="primary" />;
      default:
        return <DescriptionIcon />;
    }
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        {searchParams.get('job') ? `Documents from Job ${searchParams.get('job')}` : 'Documents'}
      </Typography>

      {/* Statistics Cards */}
      {stats && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Documents
                </Typography>
                <Typography variant="h5">{stats.total_documents}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  PDF Documents
                </Typography>
                <Typography variant="h5">{stats.pdf_documents}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  URL Documents
                </Typography>
                <Typography variant="h5">{stats.url_documents}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Size
                </Typography>
                <Typography variant="h5">{formatBytes(stats.total_size_bytes)}</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Search Bar */}
      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search documents by filename, job name, or user..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              handleSearch();
            }
          }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <Button onClick={handleSearch} disabled={searching}>
                  {searching ? <CircularProgress size={20} /> : 'Search'}
                </Button>
                {searchQuery && (
                  <Button
                    onClick={() => {
                      setSearchQuery('');
                      loadDocuments();
                    }}
                  >
                    Clear
                  </Button>
                )}
              </InputAdornment>
            ),
          }}
        />
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : documents.length === 0 ? (
        <Alert severity="info">
          {searchQuery ? 'No documents found matching your search.' : 'No documents available.'}
        </Alert>
      ) : (
        <>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Type</TableCell>
                  <TableCell>Filename</TableCell>
                  <TableCell>Job Name</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>Processed</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {documents.map((doc) => (
                  <TableRow key={doc.document_id} hover>
                    <TableCell>{getSourceIcon(doc.source_type)}</TableCell>
                    <TableCell>
                      <Box>
                        <Typography variant="body2">{doc.filename}</Typography>
                        {doc.match_field && (
                          <Chip
                            label={`Match: ${doc.match_field}`}
                            size="small"
                            color="primary"
                            sx={{ mt: 0.5 }}
                          />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>{doc.job_name}</TableCell>
                    <TableCell>{formatBytes(doc.file_size)}</TableCell>
                    <TableCell>{formatDate(doc.processed_at)}</TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => handleViewDocument(doc.document_id)}
                        title="View Document"
                      >
                        <VisibilityIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="secondary"
                        onClick={() => handleDownload(doc.document_id, doc.filename, 'markdown')}
                        title="Download Markdown"
                      >
                        <DownloadIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(e, value) => setPage(value)}
                color="primary"
              />
            </Box>
          )}
        </>
      )}
    </Container>
  );
};

export default DocumentsPage;
