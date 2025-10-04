import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  TextField,
  InputAdornment,
  Button,
  CircularProgress,
  Alert,
  Pagination,
  Grid,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  IconButton,
  Chip,
} from '@mui/material';
import {
  Search as SearchIcon,
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
  Description as DescriptionIcon,
  PictureAsPdf as PdfIcon,
  Language as LanguageIcon,
  MoreVert as MoreVertIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getCurrentUser } from 'aws-amplify/auth';
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

  // Menu and dialog state
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState<Document | null>(null);

  // User email mapping
  const [userEmails, setUserEmails] = useState<Record<string, string>>({});

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

      // Load user emails for the documents
      await loadUserEmails(filteredDocuments);
    } catch (err: any) {
      console.error('Failed to load documents:', err);
      setError(err.message || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const loadUserEmails = async (docs: Document[]) => {
    const uniqueUserIds = Array.from(new Set(docs.map(doc => doc.user_id)));
    
    for (const userId of uniqueUserIds) {
      if (!userEmails[userId]) {
        try {
          const currentUser = await getCurrentUser();
          if (currentUser.userId === userId) {
            const email = currentUser.signInDetails?.loginId || userId;
            setUserEmails(prev => ({ ...prev, [userId]: email }));
          } else {
            // For other users, show truncated ID
            const truncatedId = userId.length > 8 ? `${userId.substring(0, 8)}...` : userId;
            setUserEmails(prev => ({ ...prev, [userId]: truncatedId }));
          }
        } catch (error) {
          // If we can't get current user, just show truncated ID
          const truncatedId = userId.length > 8 ? `${userId.substring(0, 8)}...` : userId;
          setUserEmails(prev => ({ ...prev, [userId]: truncatedId }));
        }
      }
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

    if (bytes < 1024 * 1024) { // Under 1 MB - show whole numbers
      return Math.round(bytes / Math.pow(k, i)) + ' ' + sizes[i];
    } else { // 1 MB or over - show one decimal
      return Math.round((bytes / Math.pow(k, i)) * 10) / 10 + ' ' + sizes[i];
    }
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

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, document: Document) => {
    setAnchorEl(event.currentTarget);
    setSelectedDocument(document);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedDocument(null);
  };

  const handleDeleteClick = (document: Document) => {
    setDocumentToDelete(document);
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const handleDeleteConfirm = async () => {
    if (!documentToDelete) return;

    try {
      // TODO: Implement delete API call
      // await api.deleteDocument(documentToDelete.document_id);
      console.log('Delete document:', documentToDelete.document_id);
      await loadDocuments(); // Refresh the list
      setDeleteDialogOpen(false);
      setDocumentToDelete(null);
    } catch (error) {
      console.error('Error deleting document:', error);
      // TODO: Show error snackbar
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setDocumentToDelete(null);
  };

  const columns: GridColDef[] = [
    {
      field: 'type',
      headerName: 'Type',
      width: 80,
      sortable: false,
      renderCell: (params) => getSourceIcon(params.row.source_type),
    },
    {
      field: 'job_name',
      headerName: 'Job Name',
      width: 200,
      sortable: true,
    },
    {
      field: 'filename',
      headerName: 'Filename',
      width: 250,
      sortable: true,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', height: '100%' }}>
          <Typography
            variant="body2"
            sx={{
              cursor: 'pointer',
              color: 'primary.main',
              textDecoration: 'underline',
              '&:hover': { color: 'primary.dark' }
            }}
            onClick={() => handleViewDocument(params.row.document_id)}
          >
            {params.value}
          </Typography>
          {params.row.match_field && (
            <Chip
              label={`Match: ${params.row.match_field}`}
              size="small"
              color="primary"
              sx={{ mt: 0.5, ml: 1 }}
            />
          )}
        </Box>
      ),
    },
    {
      field: 'file_size',
      headerName: 'Size',
      width: 100,
      sortable: true,
      renderCell: (params) => formatBytes(params.value),
    },
    {
      field: 'processed_at',
      headerName: 'Processed',
      width: 180,
      sortable: true,
      renderCell: (params) => formatDate(params.value),
    },
    {
      field: 'user_id',
      headerName: 'User',
      width: 150,
      sortable: true,
      renderCell: (params) => userEmails[params.value] || 'Loading...',
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 80,
      sortable: false,
      renderCell: (params) => (
        <IconButton
          size="small"
          onClick={(event) => handleMenuOpen(event, params.row)}
        >
          <MoreVertIcon />
        </IconButton>
      ),
    },
  ];

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        {searchParams.get('job') ? `Documents from Job ${searchParams.get('job')}` : 'Processed Documents'}
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
          <DataGrid
            rows={documents}
            columns={columns}
            getRowId={(row) => row.document_id}
            initialState={{
              pagination: {
                paginationModel: { pageSize: docsPerPage },
              },
            }}
            pageSizeOptions={[docsPerPage]}
            disableRowSelectionOnClick
            disableColumnFilter
            disableColumnSelector
            disableDensitySelector
            hideFooterPagination
            autoHeight
            sx={{
              '& .MuiDataGrid-cell:focus': {
                outline: 'none',
              },
              '& .MuiDataGrid-row:hover': {
                backgroundColor: 'action.hover',
              },
              '& .MuiDataGrid-cell': {
                padding: '8px 16px',
              },
              '& .MuiDataGrid-row': {
                minHeight: '48px !important',
              },
            }}
          />

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

      {/* Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => {
          if (selectedDocument) {
            handleViewDocument(selectedDocument.document_id);
            handleMenuClose();
          }
        }}>
          <ListItemIcon>
            <VisibilityIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => {
          if (selectedDocument) {
            handleDownload(selectedDocument.document_id, selectedDocument.filename, 'markdown');
            handleMenuClose();
          }
        }}>
          <ListItemIcon>
            <DownloadIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Download</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => {
          if (selectedDocument) {
            handleDeleteClick(selectedDocument);
          }
        }}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText sx={{ color: 'error.main' }}>Delete</ListItemText>
        </MenuItem>
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
      >
        <DialogTitle>Delete Document</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete "{documentToDelete?.filename}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default DocumentsPage;
