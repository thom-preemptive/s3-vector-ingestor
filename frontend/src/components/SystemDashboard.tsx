import React, { useState, useEffect } from 'react';
import {
    Box,
    Grid,
    Card,
    CardContent,
    Typography,
    CircularProgress,
    Alert,
    Chip,
    LinearProgress,
    IconButton,
    Tooltip,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow
} from '@mui/material';
import { 
    Refresh as RefreshIcon, 
    Warning as WarningIcon, 
    CheckCircle as CheckCircleIcon, 
    Error as ErrorIcon, 
    HourglassEmpty as HourglassEmptyIcon 
} from '@mui/icons-material';

interface SystemHealth {
    timestamp: string;
    health_status: 'healthy' | 'warning' | 'critical';
    health_score: number;
    issues: string[];
    metrics: {
        total_dlq_messages: number;
        active_workers: number;
        queue_count: number;
    };
}

interface QueueStats {
    timestamp: string;
    queues: {
        [queueName: string]: {
            sqs_queue: {
                visible_messages: number;
                in_flight_messages: number;
                delayed_messages: number;
            };
            dead_letter_queue: {
                messages: number;
            };
            job_status_counts: {
                [status: string]: number;
            };
            total_jobs: number;
            queue_health: 'healthy' | 'warning' | 'critical';
        };
    };
    overall_health: string;
    total_dlq_messages: number;
}

interface WorkerStatus {
    timestamp: string;
    active_worker_count: number;
    workers: Array<{
        worker_id: string;
        active_jobs: Array<{
            job_id: string;
            queue_type: string;
            started_at: string;
            duration: number;
        }>;
        job_count: number;
        queue_types: string[];
        average_job_duration?: number;
        longest_running_job?: {
            job_id: string;
            duration: number;
        };
    }>;
}

interface DashboardOverview {
    timestamp: string;
    summary: {
        jobs_queued: number;
        jobs_processing: number;
        jobs_completed_today: number;
        active_workers: number;
        queue_health: string;
    };
    queue_statistics: QueueStats;
    worker_status: WorkerStatus;
}

const SystemDashboard: React.FC = () => {
    const [overview, setOverview] = useState<DashboardOverview | null>(null);
    const [health, setHealth] = useState<SystemHealth | null>(null);
    const [loading, setLoading] = useState(true);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
    const [autoRefresh, setAutoRefresh] = useState(true);

    const fetchDashboardData = async () => {
        try {
            const token = localStorage.getItem('access_token');
            const headers = {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            };

            const [overviewResponse, healthResponse] = await Promise.all([
                fetch('/api/dashboard/overview', { headers }),
                fetch('/api/dashboard/health', { headers })
            ]);

            if (overviewResponse.ok && healthResponse.ok) {
                const overviewData = await overviewResponse.json();
                const healthData = await healthResponse.json();
                
                setOverview(overviewData);
                setHealth(healthData);
                setLastUpdated(new Date());
            }
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDashboardData();
        
        if (autoRefresh) {
            const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30 seconds
            return () => clearInterval(interval);
        }
    }, [autoRefresh]);

    const getHealthColor = (status: string) => {
        switch (status) {
            case 'healthy': return 'success';
            case 'warning': return 'warning';
            case 'critical': return 'error';
            default: return 'primary';
        }
    };

    const getHealthIcon = (status: string) => {
        switch (status) {
            case 'healthy': return <CheckCircleIcon color="success" />;
            case 'warning': return <WarningIcon color="warning" />;
            case 'critical': return <ErrorIcon color="error" />;
            default: return <HourglassEmptyIcon />;
        }
    };

    const formatDuration = (seconds: number): string => {
        if (seconds < 60) return `${Math.round(seconds)}s`;
        if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
        return `${Math.round(seconds / 3600)}h`;
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h4" component="h1">
                    System Dashboard
                </Typography>
                <Box display="flex" alignItems="center" gap={2}>
                    {lastUpdated && (
                        <Typography variant="body2" color="text.secondary">
                            Last updated: {lastUpdated.toLocaleTimeString()}
                        </Typography>
                    )}
                    <Tooltip title="Refresh Dashboard">
                        <IconButton onClick={fetchDashboardData}>
                            <RefreshIcon />
                        </IconButton>
                    </Tooltip>
                </Box>
            </Box>

            {/* System Health Alert */}
            {health && health.health_status !== 'healthy' && (
                <Alert 
                    severity={health.health_status === 'warning' ? 'warning' : 'error'} 
                    sx={{ mb: 3 }}
                >
                    <Typography variant="h6">System Health Issues Detected</Typography>
                    <ul>
                        {health.issues.map((issue, index) => (
                            <li key={index}>{issue}</li>
                        ))}
                    </ul>
                </Alert>
            )}

            {/* Summary Cards */}
            <Grid container spacing={3} mb={3}>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Box display="flex" alignItems="center" justifyContent="space-between">
                                <Box>
                                    <Typography color="text.secondary" gutterBottom>
                                        Jobs Queued
                                    </Typography>
                                    <Typography variant="h4">
                                        {overview?.summary.jobs_queued || 0}
                                    </Typography>
                                </Box>
                                <HourglassEmptyIcon color="primary" fontSize="large" />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Box display="flex" alignItems="center" justifyContent="space-between">
                                <Box>
                                    <Typography color="text.secondary" gutterBottom>
                                        Jobs Processing
                                    </Typography>
                                    <Typography variant="h4">
                                        {overview?.summary.jobs_processing || 0}
                                    </Typography>
                                </Box>
                                <CircularProgress size={40} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Box display="flex" alignItems="center" justifyContent="space-between">
                                <Box>
                                    <Typography color="text.secondary" gutterBottom>
                                        Completed Today
                                    </Typography>
                                    <Typography variant="h4">
                                        {overview?.summary.jobs_completed_today || 0}
                                    </Typography>
                                </Box>
                                <CheckCircleIcon color="success" fontSize="large" />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Box display="flex" alignItems="center" justifyContent="space-between">
                                <Box>
                                    <Typography color="text.secondary" gutterBottom>
                                        Active Workers
                                    </Typography>
                                    <Typography variant="h4">
                                        {overview?.summary.active_workers || 0}
                                    </Typography>
                                </Box>
                                {getHealthIcon(overview?.summary.queue_health || 'unknown')}
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* System Health Score */}
            {health && (
                <Card sx={{ mb: 3 }}>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            System Health Score
                        </Typography>
                        <Box display="flex" alignItems="center" gap={2} mb={2}>
                            <LinearProgress 
                                variant="determinate" 
                                value={health.health_score} 
                                sx={{ flexGrow: 1, height: 10, borderRadius: 5 }}
                                color={getHealthColor(health.health_status)}
                            />
                            <Typography variant="h6">
                                {Math.round(health.health_score)}%
                            </Typography>
                            <Chip 
                                label={health.health_status.toUpperCase()} 
                                color={getHealthColor(health.health_status)}
                                icon={getHealthIcon(health.health_status)}
                            />
                        </Box>
                    </CardContent>
                </Card>
            )}

            {/* Queue Statistics */}
            <Grid container spacing={3} mb={3}>
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Queue Status
                            </Typography>
                            <TableContainer>
                                <Table size="small">
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>Queue</TableCell>
                                            <TableCell align="right">Queued</TableCell>
                                            <TableCell align="right">Processing</TableCell>
                                            <TableCell align="right">DLQ</TableCell>
                                            <TableCell>Health</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {overview && Object.entries(overview.queue_statistics.queues).map(([queueName, queueData]) => (
                                            <TableRow key={queueName}>
                                                <TableCell>
                                                    <Typography variant="body2">
                                                        {queueName.replace('_', ' ').toUpperCase()}
                                                    </Typography>
                                                </TableCell>
                                                <TableCell align="right">
                                                    {queueData.sqs_queue.visible_messages}
                                                </TableCell>
                                                <TableCell align="right">
                                                    {queueData.sqs_queue.in_flight_messages}
                                                </TableCell>
                                                <TableCell align="right">
                                                    <Box display="flex" alignItems="center" justifyContent="flex-end">
                                                        {queueData.dead_letter_queue.messages}
                                                        {queueData.dead_letter_queue.messages > 0 && (
                                                            <WarningIcon color="warning" fontSize="small" sx={{ ml: 1 }} />
                                                        )}
                                                    </Box>
                                                </TableCell>
                                                <TableCell>
                                                    <Chip 
                                                        label={queueData.queue_health} 
                                                        color={getHealthColor(queueData.queue_health)}
                                                        size="small"
                                                    />
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Active Workers
                            </Typography>
                            {overview?.worker_status.workers.length === 0 ? (
                                <Typography color="text.secondary">
                                    No active workers detected
                                </Typography>
                            ) : (
                                <TableContainer>
                                    <Table size="small">
                                        <TableHead>
                                            <TableRow>
                                                <TableCell>Worker ID</TableCell>
                                                <TableCell align="right">Jobs</TableCell>
                                                <TableCell align="right">Avg Duration</TableCell>
                                                <TableCell>Queue Types</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {overview?.worker_status.workers.map((worker) => (
                                                <TableRow key={worker.worker_id}>
                                                    <TableCell>
                                                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                                                            {worker.worker_id.substring(0, 8)}...
                                                        </Typography>
                                                    </TableCell>
                                                    <TableCell align="right">
                                                        {worker.job_count}
                                                    </TableCell>
                                                    <TableCell align="right">
                                                        {worker.average_job_duration ? 
                                                            formatDuration(worker.average_job_duration) : 
                                                            'N/A'
                                                        }
                                                    </TableCell>
                                                    <TableCell>
                                                        <Box display="flex" gap={0.5} flexWrap="wrap">
                                                            {worker.queue_types.map((queueType) => (
                                                                <Chip 
                                                                    key={queueType}
                                                                    label={queueType.replace('_', ' ')}
                                                                    size="small"
                                                                    variant="outlined"
                                                                />
                                                            ))}
                                                        </Box>
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </TableContainer>
                            )}
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
};

export default SystemDashboard;