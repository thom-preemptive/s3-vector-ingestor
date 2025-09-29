import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Button,
} from '@mui/material';
import {
  Assignment as JobsIcon,
  CheckCircle as CompletedIcon,
  Schedule as PendingIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';

const Dashboard: React.FC = () => {
  const [stats] = React.useState({
    totalJobs: 12,
    completedJobs: 8,
    pendingJobs: 3,
    errorJobs: 1,
  });

  const [recentJobs] = React.useState([
    {
      id: '1',
      name: 'Emergency Response Q4',
      status: 'completed',
      documentsProcessed: 15,
      createdAt: '2024-01-15T10:30:00Z',
    },
    {
      id: '2', 
      name: 'Training Materials',
      status: 'processing',
      documentsProcessed: 8,
      createdAt: '2024-01-14T14:22:00Z',
    },
  ]);

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
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <JobsIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Total Jobs</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {stats.totalJobs}
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
              <Typography variant="h4" color="success.main">
                {stats.completedJobs}
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
              <Typography variant="h4" color="warning.main">
                {stats.pendingJobs}
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
              <Typography variant="h4" color="error.main">
                {stats.errorJobs}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Recent Jobs
        </Typography>
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
                          {job.documentsProcessed} documents processed
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Created: {new Date(job.createdAt).toLocaleDateString()}
                        </Typography>
                      </Box>
                    </Box>
                    <Box>
                      <Chip 
                        label={job.status} 
                        color={getStatusColor(job.status) as any}
                        sx={{ mr: 2 }}
                      />
                      <Button variant="outlined" size="small">
                        View Details
                      </Button>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>
    </Box>
  );
};

export default Dashboard;