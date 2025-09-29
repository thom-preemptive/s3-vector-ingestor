import React, { useState, useEffect } from 'react';

interface Job {
    job_id: string;
    queue_type: string;
    status: string;
    priority: number;
    user_id: string;
    created_at: string;
    updated_at: string;
    processing_started_at?: string;
    processing_completed_at?: string;
    error_message?: string;
    assigned_worker?: string;
    retry_count: number;
    max_retries: number;
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
            queue_health: string;
        };
    };
    overall_health: string;
    total_dlq_messages: number;
}

const JobMonitoringDashboard: React.FC = () => {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [queueStats, setQueueStats] = useState<QueueStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

    const fetchData = async () => {
        try {
            const token = localStorage.getItem('access_token');
            const headers = {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            };

            const [jobsResponse, queueResponse] = await Promise.all([
                fetch('/api/dashboard/jobs?limit=20', { headers }),
                fetch('/api/dashboard/queues', { headers })
            ]);

            if (jobsResponse.ok && queueResponse.ok) {
                const jobsData = await jobsResponse.json();
                const queueData = await queueResponse.json();
                
                setJobs(jobsData.jobs || []);
                setQueueStats(queueData);
                setLastUpdated(new Date());
            }
        } catch (error) {
            console.error('Error fetching monitoring data:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000); // Refresh every 10 seconds
        return () => clearInterval(interval);
    }, []);

    const getStatusColor = (status: string): string => {
        switch (status) {
            case 'completed': return '#4caf50';
            case 'processing': return '#2196f3';
            case 'queued': return '#ff9800';
            case 'failed': return '#f44336';
            case 'cancelled': return '#9e9e9e';
            case 'pending_approval': return '#9c27b0';
            case 'approved': return '#4caf50';
            case 'rejected': return '#f44336';
            default: return '#757575';
        }
    };

    const formatTimestamp = (timestamp: string): string => {
        const date = new Date(timestamp);
        return date.toLocaleString();
    };

    const formatDuration = (startTime: string, endTime?: string): string => {
        const start = new Date(startTime);
        const end = endTime ? new Date(endTime) : new Date();
        const duration = Math.round((end.getTime() - start.getTime()) / 1000);
        
        if (duration < 60) return `${duration}s`;
        if (duration < 3600) return `${Math.round(duration / 60)}m`;
        return `${Math.round(duration / 3600)}h`;
    };

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                <div>Loading...</div>
            </div>
        );
    }

    return (
        <div style={{ padding: '1rem', fontFamily: 'Arial, sans-serif' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <h1 style={{ margin: 0 }}>Job Monitoring Dashboard</h1>
                <div style={{ fontSize: '0.875rem', color: '#666' }}>
                    Last updated: {lastUpdated?.toLocaleTimeString()}
                </div>
            </div>

            {/* Queue Statistics */}
            <div style={{ marginBottom: '2rem' }}>
                <h2>Queue Statistics</h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
                    {queueStats && Object.entries(queueStats.queues).map(([queueName, queueData]) => (
                        <div 
                            key={queueName}
                            style={{ 
                                border: '1px solid #ddd', 
                                borderRadius: '8px', 
                                padding: '1rem',
                                backgroundColor: queueData.queue_health === 'healthy' ? '#f8f9fa' : '#fff3cd'
                            }}
                        >
                            <h3 style={{ margin: '0 0 1rem 0', textTransform: 'capitalize' }}>
                                {queueName.replace('_', ' ')}
                            </h3>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.875rem' }}>
                                <div>Queued: <strong>{queueData.sqs_queue.visible_messages}</strong></div>
                                <div>Processing: <strong>{queueData.sqs_queue.in_flight_messages}</strong></div>
                                <div>Delayed: <strong>{queueData.sqs_queue.delayed_messages}</strong></div>
                                <div>DLQ: <strong style={{ color: queueData.dead_letter_queue.messages > 0 ? '#f44336' : 'inherit' }}>
                                    {queueData.dead_letter_queue.messages}
                                </strong></div>
                            </div>
                            <div style={{ marginTop: '0.5rem' }}>
                                <span 
                                    style={{ 
                                        padding: '0.25rem 0.5rem', 
                                        borderRadius: '4px', 
                                        fontSize: '0.75rem',
                                        backgroundColor: queueData.queue_health === 'healthy' ? '#4caf50' : '#ff9800',
                                        color: 'white'
                                    }}
                                >
                                    {queueData.queue_health.toUpperCase()}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Recent Jobs */}
            <div>
                <h2>Recent Jobs</h2>
                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                        <thead>
                            <tr style={{ backgroundColor: '#f5f5f5' }}>
                                <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Job ID</th>
                                <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Queue</th>
                                <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Status</th>
                                <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Priority</th>
                                <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Created</th>
                                <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Duration</th>
                                <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Worker</th>
                                <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Retries</th>
                            </tr>
                        </thead>
                        <tbody>
                            {jobs.map((job) => (
                                <tr key={job.job_id} style={{ borderBottom: '1px solid #eee' }}>
                                    <td style={{ padding: '0.75rem', fontFamily: 'monospace' }}>
                                        {job.job_id.substring(0, 8)}...
                                    </td>
                                    <td style={{ padding: '0.75rem', textTransform: 'capitalize' }}>
                                        {job.queue_type.replace('_', ' ')}
                                    </td>
                                    <td style={{ padding: '0.75rem' }}>
                                        <span 
                                            style={{ 
                                                padding: '0.25rem 0.5rem', 
                                                borderRadius: '4px', 
                                                color: 'white',
                                                backgroundColor: getStatusColor(job.status),
                                                fontSize: '0.75rem'
                                            }}
                                        >
                                            {job.status.toUpperCase()}
                                        </span>
                                    </td>
                                    <td style={{ padding: '0.75rem' }}>
                                        <div style={{ display: 'flex', alignItems: 'center' }}>
                                            {'★'.repeat(job.priority)}
                                            <span style={{ marginLeft: '0.25rem', color: '#666' }}>
                                                ({job.priority})
                                            </span>
                                        </div>
                                    </td>
                                    <td style={{ padding: '0.75rem' }}>
                                        {formatTimestamp(job.created_at)}
                                    </td>
                                    <td style={{ padding: '0.75rem' }}>
                                        {job.processing_started_at ? 
                                            formatDuration(job.processing_started_at, job.processing_completed_at) : 
                                            '-'
                                        }
                                    </td>
                                    <td style={{ padding: '0.75rem', fontFamily: 'monospace' }}>
                                        {job.assigned_worker ? 
                                            job.assigned_worker.substring(0, 8) + '...' : 
                                            '-'
                                        }
                                    </td>
                                    <td style={{ padding: '0.75rem' }}>
                                        <span style={{ color: job.retry_count > 0 ? '#ff9800' : 'inherit' }}>
                                            {job.retry_count}/{job.max_retries}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                
                {jobs.length === 0 && (
                    <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
                        No recent jobs found
                    </div>
                )}
            </div>
        </div>
    );
};

export default JobMonitoringDashboard;