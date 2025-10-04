import React, { useEffect, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Button,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Assignment as JobsIcon,
  CheckCircle as CompletedIcon,
  Schedule as PendingIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

interface DashboardStats {
  total_jobs: number;
  completed_jobs: number;
  pending_jobs: number;
  error_jobs: number;
}

interface RecentJob {
  id: string;
  name: string;
  status: string;
  documents_processed: number;
  created_at: string;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats>({
    total_jobs: 0,
    completed_jobs: 0,
    pending_jobs: 0,
    error_jobs: 0,
  });
  const [recentJobs, setRecentJobs] = useState<RecentJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch both stats and recent jobs
      const [statsData, jobsData] = await Promise.all([
        api.getDashboardStats(),
        api.getDashboardRecentJobs(5)
      ]);
      
      setStats(statsData);
      setRecentJobs(jobsData.jobs || []);
    } catch (err: any) {
      console.error('Failed to load dashboard data:', err);
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
    
    // Refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CompletedIcon color="success" />;
      case 'processing':
        return <PendingIcon color="warning" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <JobsIcon />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Dashboard
        </Typography>
        <Button
          variant="outlined"
          startIcon={loading ? <CircularProgress size={20} /> : <RefreshIcon />}
          onClick={loadDashboardData}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading && !stats.total_jobs && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <JobsIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Total Jobs</Typography>
              </Box>
                            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                {stats.total_jobs}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CompletedIcon sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6">Completed</Typography>
              </Box>
                            <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'success.main' }}>
                {stats.completed_jobs}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <PendingIcon sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="h6">Pending</Typography>
              </Box>
                            <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'warning.main' }}>
                {stats.pending_jobs}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ErrorIcon sx={{ mr: 1, color: 'error.main' }} />
                <Typography variant="h6">Errors</Typography>
              </Box>
                            <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'error.main' }}>
                {stats.error_jobs}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Recent Jobs
        </Typography>
        {recentJobs.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body1" color="text.secondary">
              No recent jobs found. Upload documents to get started.
            </Typography>
            <Button 
              variant="contained" 
              sx={{ mt: 2 }}
              onClick={() => navigate('/upload')}
            >
              Upload Documents
            </Button>
          </Box>
        ) : (
          <Grid container spacing={2}>
            {recentJobs.map((job) => (
              <Grid item xs={12} key={job.id}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {getStatusIcon(job.status)}
                        <Box sx={{ ml: 2 }}>
                          <Typography variant="h6">{job.name}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            {job.documents_processed} documents processed
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Created: {new Date(job.created_at).toLocaleDateString()}
                          </Typography>
                        </Box>
                      </Box>
                      <Box>
                        <Chip 
                          label={job.status} 
                          color={getStatusColor(job.status) as any}
                          sx={{ mr: 2 }}
                        />
                        <Button 
                          variant="outlined" 
                          size="small"
                          onClick={() => navigate(`/documents/${job.id}`)}
                        >
                          View Details
                        </Button>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Paper>
    </Box>
  );
};

export default Dashboard;