"""
Dashboard API Endpoints

Provides real-time monitoring and management capabilities for the emergency document processor.
Includes job queue status, system health metrics, and operational dashboards.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta

from services.aws_services import CognitoService
from services.queue_service import JobQueueService, QueueType, JobStatus, JobPriority

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Initialize services
queue_service = JobQueueService()
cognito_service = CognitoService()

# Authentication
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Get current user from JWT token - simplified for testing"""
    if not credentials:
        return {"user_id": "anonymous", "username": "anonymous"}
    
    try:
        # For now, return a test user - in production this would validate the JWT
        return {
            "user_id": "test-user",
            "username": "test-user",
            "email": "test@example.com"
        }
    except Exception as e:
        return {"user_id": "anonymous", "username": "anonymous"}

@router.get("/health")
async def get_system_health():
    """Get overall system health status"""
    try:
        # Get queue statistics
        queue_stats = await queue_service.get_queue_statistics()
        
        # Get active workers
        workers = await queue_service.get_active_workers()
        
        # Calculate system health score
        health_score = 100
        issues = []
        
        # Check for DLQ messages
        total_dlq = queue_stats.get('total_dlq_messages', 0)
        if total_dlq > 0:
            health_score -= min(50, total_dlq * 10)
            issues.append(f"{total_dlq} messages in dead letter queues")
        
        # Check for worker activity
        active_workers = workers.get('active_worker_count', 0)
        if active_workers == 0:
            health_score -= 30
            issues.append("No active workers detected")
        
        # Check for queue backlogs
        for queue_name, queue_data in queue_stats.get('queues', {}).items():
            visible = queue_data['sqs_queue']['visible_messages']
            if visible > 100:  # Threshold for backlog
                health_score -= min(20, (visible - 100) / 10)
                issues.append(f"{queue_name} queue has {visible} pending messages")
        
        health_status = "healthy" if health_score >= 80 else "warning" if health_score >= 50 else "critical"
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "health_status": health_status,
            "health_score": max(0, health_score),
            "issues": issues,
            "metrics": {
                "total_dlq_messages": total_dlq,
                "active_workers": active_workers,
                "queue_count": len(queue_stats.get('queues', {}))
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")

@router.get("/overview")
async def get_dashboard_overview():
    """Get comprehensive dashboard overview"""
    try:
        # Get all metrics in parallel
        queue_stats_task = queue_service.get_queue_statistics()
        workers_task = queue_service.get_active_workers()
        
        queue_stats, workers = await asyncio.gather(queue_stats_task, workers_task)
        
        # Calculate summary metrics
        total_queued = 0
        total_processing = 0
        total_completed_today = 0
        
        today = datetime.utcnow().date()
        
        for queue_data in queue_stats.get('queues', {}).values():
            total_queued += queue_data['sqs_queue']['visible_messages']
            total_processing += queue_data['sqs_queue']['in_flight_messages']
            
            # Count completed jobs today (from job status counts)
            job_counts = queue_data.get('job_status_counts', {})
            total_completed_today += job_counts.get('completed', 0)  # This is approximate
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "jobs_queued": total_queued,
                "jobs_processing": total_processing,
                "jobs_completed_today": total_completed_today,
                "active_workers": workers.get('active_worker_count', 0),
                "queue_health": queue_stats.get('overall_health', 'unknown')
            },
            "queue_statistics": queue_stats,
            "worker_status": workers
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard overview: {str(e)}")

@router.get("/queues")
async def get_queue_status(queue_type: Optional[str] = Query(None)):
    """Get detailed queue status and metrics"""
    try:
        qt = QueueType(queue_type) if queue_type else None
        stats = await queue_service.get_queue_statistics(qt)
        return stats
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid queue type: {queue_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {str(e)}")

@router.get("/queues/{queue_type}/jobs")
async def get_queue_jobs(
    queue_type: str,
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200)
):
    """Get jobs for a specific queue"""
    try:
        qt = QueueType(queue_type)
        job_status = JobStatus(status) if status else None
        
        # Note: This is a simplified implementation
        # In a real system, you'd want to query jobs by queue_type efficiently
        jobs = []  # Placeholder - would need to implement queue-specific job queries
        
        return {
            "queue_type": queue_type,
            "status_filter": status,
            "jobs": jobs,
            "total_count": len(jobs)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue jobs: {str(e)}")

@router.get("/workers")
async def get_worker_status():
    """Get detailed worker status and performance metrics"""
    try:
        workers = await queue_service.get_active_workers()
        
        # Add performance metrics for each worker
        for worker in workers.get('workers', []):
            # Calculate average job duration
            if worker['active_jobs']:
                total_duration = sum(job['duration'] for job in worker['active_jobs'])
                worker['average_job_duration'] = total_duration / len(worker['active_jobs'])
                worker['longest_running_job'] = max(worker['active_jobs'], key=lambda x: x['duration'])
            else:
                worker['average_job_duration'] = 0
                worker['longest_running_job'] = None
        
        return workers
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get worker status: {str(e)}")

@router.get("/jobs/{job_id}")
async def get_job_details(job_id: str):
    """Get detailed information about a specific job"""
    try:
        job = await queue_service.get_job_status(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job details: {str(e)}")

@router.get("/jobs")
async def get_jobs(
    user_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    queue_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    current_user: dict = Depends(get_current_user)
):
    """Get jobs with filtering options"""
    try:
        # If no user_id specified, use current user
        if not user_id:
            user_id = current_user.get('sub')
        
        # Parse optional filters
        job_status = JobStatus(status) if status else None
        
        # Get user jobs
        jobs = await queue_service.get_user_jobs(user_id, job_status, limit)
        
        # Filter by queue type if specified
        if queue_type:
            qt = QueueType(queue_type)
            jobs = [job for job in jobs if job.queue_type == qt]
        
        return {
            "user_id": user_id,
            "filters": {
                "status": status,
                "queue_type": queue_type
            },
            "jobs": [job.to_dict() for job in jobs],
            "total_count": len(jobs)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get jobs: {str(e)}")

@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a queued or processing job"""
    try:
        # Get job details
        job = await queue_service.get_job_status(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if user owns the job (or is admin)
        if job.user_id != current_user.get('sub'):
            # Check if user has admin privileges
            user_groups = current_user.get('cognito:groups', [])
            if 'admin' not in user_groups:
                raise HTTPException(status_code=403, detail="Not authorized to cancel this job")
        
        # Check if job can be cancelled
        if job.status not in [JobStatus.QUEUED, JobStatus.PROCESSING]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel job with status: {job.status.value}")
        
        # Cancel the job
        success = await queue_service.fail_job(job_id, "Cancelled by user", retry=False)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to cancel job")
        
        return {"message": "Job cancelled successfully", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")

@router.get("/metrics/performance")
async def get_performance_metrics(
    hours: int = Query(24, ge=1, le=168)  # Last 1-168 hours
):
    """Get system performance metrics over time"""
    try:
        # This would typically query CloudWatch metrics
        # For now, we'll return mock data structure
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Mock performance data - in real implementation, query CloudWatch
        metrics = {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "throughput": {
                "jobs_per_hour": [
                    {"timestamp": (end_time - timedelta(hours=i)).isoformat(), "count": 45 + (i % 10)}
                    for i in range(hours, 0, -1)
                ],
                "average_jobs_per_hour": 47.2
            },
            "latency": {
                "average_processing_time": 125.5,  # seconds
                "p95_processing_time": 340.2,
                "p99_processing_time": 890.1
            },
            "error_rates": {
                "success_rate": 98.7,
                "retry_rate": 1.8,
                "failure_rate": 0.5
            },
            "resource_utilization": {
                "active_workers": 3,
                "peak_workers": 5,
                "average_cpu_usage": 65.2,
                "average_memory_usage": 72.8
            }
        }
        
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.get("/metrics/queues")
async def get_queue_metrics(
    hours: int = Query(24, ge=1, le=168)
):
    """Get queue-specific metrics over time"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Mock queue metrics - in real implementation, query CloudWatch
        queue_metrics = {}
        
        for queue_type in QueueType:
            queue_metrics[queue_type.value] = {
                "messages_sent": [
                    {"timestamp": (end_time - timedelta(hours=i)).isoformat(), "count": 20 + (i % 5)}
                    for i in range(hours, 0, -1)
                ],
                "messages_processed": [
                    {"timestamp": (end_time - timedelta(hours=i)).isoformat(), "count": 18 + (i % 4)}
                    for i in range(hours, 0, -1)
                ],
                "average_processing_time": 85.3 + (hash(queue_type.value) % 100),
                "current_backlog": hash(queue_type.value) % 20,
                "dlq_messages": 0
            }
        
        return {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "queues": queue_metrics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue metrics: {str(e)}")

@router.post("/maintenance/purge-completed")
async def purge_completed_jobs(
    days_old: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Purge completed jobs older than specified days (admin only)"""
    try:
        # Check admin privileges
        user_groups = current_user.get('cognito:groups', [])
        if 'admin' not in user_groups:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        deleted_count = await queue_service.purge_completed_jobs(days_old)
        
        return {
            "message": f"Purged {deleted_count} completed jobs older than {days_old} days",
            "deleted_count": deleted_count,
            "days_old": days_old
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to purge completed jobs: {str(e)}")

@router.get("/alerts")
async def get_system_alerts():
    """Get current system alerts and warnings"""
    try:
        alerts = []
        
        # Get queue statistics to check for issues
        queue_stats = await queue_service.get_queue_statistics()
        
        # Check for dead letter queue messages
        for queue_name, queue_data in queue_stats.get('queues', {}).items():
            dlq_count = queue_data['dead_letter_queue']['messages']
            if dlq_count > 0:
                alerts.append({
                    "severity": "warning",
                    "type": "dead_letter_queue",
                    "message": f"{queue_name} has {dlq_count} messages in dead letter queue",
                    "queue": queue_name,
                    "count": dlq_count,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Check for large queue backlogs
        for queue_name, queue_data in queue_stats.get('queues', {}).items():
            visible = queue_data['sqs_queue']['visible_messages']
            if visible > 100:
                alerts.append({
                    "severity": "info" if visible < 500 else "warning",
                    "type": "queue_backlog",
                    "message": f"{queue_name} has {visible} pending messages",
                    "queue": queue_name,
                    "count": visible,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Check for inactive workers
        workers = await queue_service.get_active_workers()
        if workers.get('active_worker_count', 0) == 0:
            alerts.append({
                "severity": "critical",
                "type": "no_workers",
                "message": "No active workers detected",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "alert_count": len(alerts),
            "alerts": alerts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system alerts: {str(e)}")