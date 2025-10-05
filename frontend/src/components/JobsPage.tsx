import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  CircularProgress,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import apiService from '../services/api';

interface Job {
  job_id: string;
  job_name: string;
  status: string;
  created_at: string;
  total_documents?: number;
  documents_processed?: number;
  approval_required?: boolean;
  approval_status?: string;
}

const JobsPage: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const data = await apiService.getJobs();
      setJobs(data.jobs || []);
    } catch (error) {
      console.error('Error fetching jobs:', error);
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 10000);
    return () => clearInterval(interval);
  }, []);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold' }}>Processing Jobs</Typography>
        <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchJobs} disabled={loading}>Refresh</Button>
      </Box>
      <Paper elevation={2}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Job ID</TableCell>
                <TableCell>Job Title</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Documents</TableCell>
                <TableCell>Created</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow><TableCell colSpan={5} sx={{ textAlign: 'center', py: 4 }}><CircularProgress /></TableCell></TableRow>
              ) : jobs.length === 0 ? (
                <TableRow><TableCell colSpan={5} sx={{ textAlign: 'center', py: 4 }}>No jobs found</TableCell></TableRow>
              ) : (
                jobs.map((job) => (
                  <TableRow key={job.job_id} hover>
                    <TableCell>{job.job_id.substring(0, 8)}...</TableCell>
                    <TableCell>{job.job_name}</TableCell>
                    <TableCell><Chip label={job.status} size="small" /></TableCell>
                    <TableCell>{job.documents_processed || 0} / {job.total_documents || 0}</TableCell>
                    <TableCell>{formatDate(job.created_at)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default JobsPage;
