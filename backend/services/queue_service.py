"""
Job Queue Service

This service manages job queuing, processing status, and queue monitoring.
It integrates with SQS for reliable job queuing and DynamoDB for persistence.
"""

import boto3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
import uuid
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"

class JobPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class QueueType(Enum):
    DOCUMENT_PROCESSING = "document_processing"
    APPROVAL_WORKFLOW = "approval_workflow"
    MAINTENANCE = "maintenance"
    MONITORING = "monitoring"

@dataclass
class QueueJob:
    job_id: str
    queue_type: QueueType
    status: JobStatus
    priority: JobPriority
    user_id: str
    created_at: str
    updated_at: str
    payload: Dict[str, Any]
    retry_count: int = 0
    max_retries: int = 3
    processing_started_at: Optional[str] = None
    processing_completed_at: Optional[str] = None
    error_message: Optional[str] = None
    assigned_worker: Optional[str] = None
    estimated_duration: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # Convert enums to values
        result['queue_type'] = self.queue_type.value
        result['status'] = self.status.value
        result['priority'] = self.priority.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueueJob':
        # Convert string values back to enums
        data['queue_type'] = QueueType(data['queue_type'])
        data['status'] = JobStatus(data['status'])
        data['priority'] = JobPriority(data['priority'])
        return cls(**data)

class JobQueueService:
    def __init__(self, region_name='us-east-1'):
        self.sqs_client = boto3.client('sqs', region_name=region_name)
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        
        # Queue configurations
        self.queue_configs = {
            QueueType.DOCUMENT_PROCESSING: {
                'queue_name': os.environ.get('DOC_PROCESSING_QUEUE', 'emergency-docs-processing'),
                'dlq_name': os.environ.get('DOC_PROCESSING_DLQ', 'emergency-docs-processing-dlq'),
                'visibility_timeout': 900,  # 15 minutes
                'max_receive_count': 3
            },
            QueueType.APPROVAL_WORKFLOW: {
                'queue_name': os.environ.get('APPROVAL_QUEUE', 'emergency-docs-approval'),
                'dlq_name': os.environ.get('APPROVAL_DLQ', 'emergency-docs-approval-dlq'),
                'visibility_timeout': 300,  # 5 minutes
                'max_receive_count': 3
            },
            QueueType.MAINTENANCE: {
                'queue_name': os.environ.get('MAINTENANCE_QUEUE', 'emergency-docs-maintenance'),
                'dlq_name': os.environ.get('MAINTENANCE_DLQ', 'emergency-docs-maintenance-dlq'),
                'visibility_timeout': 600,  # 10 minutes
                'max_receive_count': 2
            }
        }
        
        # DynamoDB table for job tracking
        self.jobs_table_name = os.environ.get('QUEUE_JOBS_TABLE', 'queue-jobs')
        self.jobs_table = self.dynamodb.Table(self.jobs_table_name)
        
    async def enqueue_job(self, 
                         queue_type: QueueType, 
                         payload: Dict[str, Any],
                         user_id: str,
                         priority: JobPriority = JobPriority.NORMAL,
                         estimated_duration: Optional[int] = None) -> str:
        """Enqueue a new job"""
        try:
            job_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            # Create job record
            job = QueueJob(
                job_id=job_id,
                queue_type=queue_type,
                status=JobStatus.QUEUED,
                priority=priority,
                user_id=user_id,
                created_at=current_time.isoformat(),
                updated_at=current_time.isoformat(),
                payload=payload,
                estimated_duration=estimated_duration
            )
            
            # Store in DynamoDB
            self.jobs_table.put_item(Item=job.to_dict())
            
            # Send to SQS queue
            queue_config = self.queue_configs[queue_type]
            queue_url = await self._get_queue_url(queue_config['queue_name'])
            
            message_body = {
                'job_id': job_id,
                'queue_type': queue_type.value,
                'priority': priority.value,
                'user_id': user_id,
                'payload': payload,
                'created_at': current_time.isoformat()
            }
            
            # Calculate delay based on priority
            delay_seconds = max(0, (4 - priority.value) * 2)  # Urgent=0s, High=2s, Normal=4s, Low=6s
            
            response = self.sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message_body),
                DelaySeconds=delay_seconds,
                MessageAttributes={
                    'Priority': {
                        'StringValue': str(priority.value),
                        'DataType': 'Number'
                    },
                    'JobType': {
                        'StringValue': queue_type.value,
                        'DataType': 'String'
                    }
                }
            )
            
            logger.info(f"Job {job_id} enqueued in {queue_type.value} queue")
            
            # Send CloudWatch metric
            await self._send_cloudwatch_metric('JobsEnqueued', 1, {
                'QueueType': queue_type.value,
                'Priority': priority.value
            })
            
            return job_id
            
        except Exception as e:
            logger.error(f"Error enqueueing job: {str(e)}")
            raise
    
    async def dequeue_job(self, queue_type: QueueType, worker_id: str) -> Optional[QueueJob]:
        """Dequeue and start processing a job"""
        try:
            queue_config = self.queue_configs[queue_type]
            queue_url = await self._get_queue_url(queue_config['queue_name'])
            
            # Receive message from SQS
            response = self.sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10,  # Long polling
                VisibilityTimeoutSeconds=queue_config['visibility_timeout'],
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            if not messages:
                return None
            
            message = messages[0]
            message_body = json.loads(message['Body'])
            job_id = message_body['job_id']
            
            # Update job status in DynamoDB
            current_time = datetime.utcnow()
            
            response = self.jobs_table.update_item(
                Key={'job_id': job_id},
                UpdateExpression="""
                    SET #status = :status,
                        updated_at = :updated,
                        processing_started_at = :started,
                        assigned_worker = :worker
                """,
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': JobStatus.PROCESSING.value,
                    ':updated': current_time.isoformat(),
                    ':started': current_time.isoformat(),
                    ':worker': worker_id
                },
                ReturnValues='ALL_NEW'
            )
            
            # Convert to QueueJob object
            job_data = response['Attributes']
            job = QueueJob.from_dict(job_data)
            
            # Store receipt handle for later deletion
            job.payload['_sqs_receipt_handle'] = message['ReceiptHandle']
            
            logger.info(f"Job {job_id} dequeued by worker {worker_id}")
            
            # Send CloudWatch metric
            await self._send_cloudwatch_metric('JobsDequeued', 1, {
                'QueueType': queue_type.value,
                'Worker': worker_id
            })
            
            return job
            
        except Exception as e:
            logger.error(f"Error dequeuing job: {str(e)}")
            raise
    
    async def complete_job(self, job_id: str, result: Dict[str, Any] = None) -> bool:
        """Mark job as completed"""
        try:
            current_time = datetime.utcnow()
            
            # Get current job to calculate duration
            response = self.jobs_table.get_item(Key={'job_id': job_id})
            if 'Item' not in response:
                raise Exception(f"Job {job_id} not found")
            
            job_data = response['Item']
            started_at = datetime.fromisoformat(job_data.get('processing_started_at', current_time.isoformat()))
            duration = (current_time - started_at).total_seconds()
            
            # Update job status
            update_expression = """
                SET #status = :status,
                    updated_at = :updated,
                    processing_completed_at = :completed
            """
            expression_values = {
                ':status': JobStatus.COMPLETED.value,
                ':updated': current_time.isoformat(),
                ':completed': current_time.isoformat()
            }
            
            if result:
                update_expression += ", result = :result"
                expression_values[':result'] = result
            
            self.jobs_table.update_item(
                Key={'job_id': job_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues=expression_values
            )
            
            # Delete message from SQS if receipt handle is available
            if result and '_sqs_receipt_handle' in result:
                queue_type = QueueType(job_data['queue_type'])
                queue_config = self.queue_configs[queue_type]
                queue_url = await self._get_queue_url(queue_config['queue_name'])
                
                self.sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=result['_sqs_receipt_handle']
                )
            
            logger.info(f"Job {job_id} completed in {duration:.2f} seconds")
            
            # Send CloudWatch metrics
            await self._send_cloudwatch_metric('JobsCompleted', 1, {
                'QueueType': job_data['queue_type']
            })
            await self._send_cloudwatch_metric('JobDuration', duration, {
                'QueueType': job_data['queue_type']
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error completing job {job_id}: {str(e)}")
            return False
    
    async def fail_job(self, job_id: str, error_message: str, retry: bool = True) -> bool:
        """Mark job as failed and optionally retry"""
        try:
            current_time = datetime.utcnow()
            
            # Get current job
            response = self.jobs_table.get_item(Key={'job_id': job_id})
            if 'Item' not in response:
                raise Exception(f"Job {job_id} not found")
            
            job_data = response['Item']
            retry_count = job_data.get('retry_count', 0)
            max_retries = job_data.get('max_retries', 3)
            
            if retry and retry_count < max_retries:
                # Increment retry count and requeue
                self.jobs_table.update_item(
                    Key={'job_id': job_id},
                    UpdateExpression="""
                        SET retry_count = :retry_count,
                            updated_at = :updated,
                            error_message = :error,
                            #status = :status
                    """,
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':retry_count': retry_count + 1,
                        ':updated': current_time.isoformat(),
                        ':error': error_message,
                        ':status': JobStatus.QUEUED.value
                    }
                )
                
                # Re-enqueue with higher priority
                queue_type = QueueType(job_data['queue_type'])
                priority = JobPriority(min(4, job_data.get('priority', 2) + 1))  # Increase priority for retries
                
                await self.enqueue_job(
                    queue_type=queue_type,
                    payload=job_data['payload'],
                    user_id=job_data['user_id'],
                    priority=priority
                )
                
                logger.info(f"Job {job_id} failed, retrying ({retry_count + 1}/{max_retries})")
                
            else:
                # Mark as permanently failed
                self.jobs_table.update_item(
                    Key={'job_id': job_id},
                    UpdateExpression="""
                        SET #status = :status,
                            updated_at = :updated,
                            error_message = :error,
                            processing_completed_at = :completed
                    """,
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': JobStatus.FAILED.value,
                        ':updated': current_time.isoformat(),
                        ':error': error_message,
                        ':completed': current_time.isoformat()
                    }
                )
                
                logger.error(f"Job {job_id} permanently failed: {error_message}")
            
            # Send CloudWatch metric
            await self._send_cloudwatch_metric('JobsFailed', 1, {
                'QueueType': job_data['queue_type'],
                'Retry': str(retry and retry_count < max_retries)
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error failing job {job_id}: {str(e)}")
            return False
    
    async def get_job_status(self, job_id: str) -> Optional[QueueJob]:
        """Get current status of a job"""
        try:
            response = self.jobs_table.get_item(Key={'job_id': job_id})
            if 'Item' not in response:
                return None
            
            return QueueJob.from_dict(response['Item'])
            
        except Exception as e:
            logger.error(f"Error getting job status {job_id}: {str(e)}")
            return None
    
    async def get_queue_statistics(self, queue_type: QueueType = None) -> Dict[str, Any]:
        """Get queue statistics and metrics"""
        try:
            stats = {
                'timestamp': datetime.utcnow().isoformat(),
                'queues': {}
            }
            
            queue_types = [queue_type] if queue_type else list(QueueType)
            
            for qt in queue_types:
                queue_config = self.queue_configs[qt]
                queue_url = await self._get_queue_url(queue_config['queue_name'])
                dlq_url = await self._get_queue_url(queue_config['dlq_name'])
                
                # Get SQS queue attributes
                queue_attrs = self.sqs_client.get_queue_attributes(
                    QueueUrl=queue_url,
                    AttributeNames=['All']
                )['Attributes']
                
                dlq_attrs = self.sqs_client.get_queue_attributes(
                    QueueUrl=dlq_url,
                    AttributeNames=['All']
                )['Attributes']
                
                # Get job counts from DynamoDB
                job_counts = await self._get_job_counts_by_status(qt)
                
                stats['queues'][qt.value] = {
                    'sqs_queue': {
                        'visible_messages': int(queue_attrs.get('ApproximateNumberOfMessages', 0)),
                        'in_flight_messages': int(queue_attrs.get('ApproximateNumberOfMessagesNotVisible', 0)),
                        'delayed_messages': int(queue_attrs.get('ApproximateNumberOfMessagesDelayed', 0))
                    },
                    'dead_letter_queue': {
                        'messages': int(dlq_attrs.get('ApproximateNumberOfMessages', 0))
                    },
                    'job_status_counts': job_counts,
                    'total_jobs': sum(job_counts.values()),
                    'queue_health': 'healthy' if int(dlq_attrs.get('ApproximateNumberOfMessages', 0)) == 0 else 'warning'
                }
            
            # Calculate overall system health
            total_dlq_messages = sum(
                q['dead_letter_queue']['messages'] 
                for q in stats['queues'].values()
            )
            
            stats['overall_health'] = 'healthy' if total_dlq_messages == 0 else 'warning'
            stats['total_dlq_messages'] = total_dlq_messages
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting queue statistics: {str(e)}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'overall_health': 'unhealthy'
            }
    
    async def get_user_jobs(self, user_id: str, status: JobStatus = None, limit: int = 50) -> List[QueueJob]:
        """Get jobs for a specific user"""
        try:
            # Query DynamoDB for user jobs
            filter_expression = None
            expression_values = {}
            
            if status:
                filter_expression = "#status = :status"
                expression_values[':status'] = status.value
            
            response = self.jobs_table.scan(
                FilterExpression=f"user_id = :user_id" + (f" AND {filter_expression}" if filter_expression else ""),
                ExpressionAttributeValues={
                    ':user_id': user_id,
                    **expression_values
                },
                ExpressionAttributeNames={'#status': 'status'} if status else None,
                Limit=limit
            )
            
            jobs = [QueueJob.from_dict(item) for item in response['Items']]
            
            # Sort by created_at descending
            jobs.sort(key=lambda x: x.created_at, reverse=True)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error getting user jobs: {str(e)}")
            return []
    
    async def get_active_workers(self) -> Dict[str, Any]:
        """Get information about active workers"""
        try:
            current_time = datetime.utcnow()
            cutoff_time = current_time - timedelta(minutes=10)  # Consider workers active if seen in last 10 minutes
            
            # Query for jobs currently being processed
            response = self.jobs_table.scan(
                FilterExpression="#status = :status AND processing_started_at > :cutoff",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': JobStatus.PROCESSING.value,
                    ':cutoff': cutoff_time.isoformat()
                }
            )
            
            workers = {}
            for item in response['Items']:
                worker_id = item.get('assigned_worker')
                if worker_id:
                    if worker_id not in workers:
                        workers[worker_id] = {
                            'worker_id': worker_id,
                            'active_jobs': [],
                            'job_count': 0,
                            'queue_types': set()
                        }
                    
                    workers[worker_id]['active_jobs'].append({
                        'job_id': item['job_id'],
                        'queue_type': item['queue_type'],
                        'started_at': item['processing_started_at'],
                        'duration': (current_time - datetime.fromisoformat(item['processing_started_at'])).total_seconds()
                    })
                    workers[worker_id]['job_count'] += 1
                    workers[worker_id]['queue_types'].add(item['queue_type'])
            
            # Convert sets to lists for JSON serialization
            for worker in workers.values():
                worker['queue_types'] = list(worker['queue_types'])
            
            return {
                'timestamp': current_time.isoformat(),
                'active_worker_count': len(workers),
                'workers': list(workers.values())
            }
            
        except Exception as e:
            logger.error(f"Error getting active workers: {str(e)}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'active_worker_count': 0,
                'workers': [],
                'error': str(e)
            }
    
    async def _get_queue_url(self, queue_name: str) -> str:
        """Get SQS queue URL"""
        try:
            response = self.sqs_client.get_queue_url(QueueName=queue_name)
            return response['QueueUrl']
        except self.sqs_client.exceptions.QueueDoesNotExist:
            # Create queue if it doesn't exist
            response = self.sqs_client.create_queue(QueueName=queue_name)
            return response['QueueUrl']
    
    async def _get_job_counts_by_status(self, queue_type: QueueType) -> Dict[str, int]:
        """Get job counts by status for a queue type"""
        try:
            counts = {status.value: 0 for status in JobStatus}
            
            response = self.jobs_table.scan(
                FilterExpression="queue_type = :queue_type",
                ExpressionAttributeValues={':queue_type': queue_type.value}
            )
            
            for item in response['Items']:
                status = item.get('status', JobStatus.QUEUED.value)
                counts[status] = counts.get(status, 0) + 1
            
            return counts
            
        except Exception as e:
            logger.error(f"Error getting job counts: {str(e)}")
            return {status.value: 0 for status in JobStatus}
    
    async def _send_cloudwatch_metric(self, metric_name: str, value: float, dimensions: Dict[str, str]):
        """Send metric to CloudWatch"""
        try:
            self.cloudwatch.put_metric_data(
                Namespace='EmergencyDocs/JobQueue',
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': value,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': k, 'Value': v} for k, v in dimensions.items()
                        ],
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Error sending CloudWatch metric: {str(e)}")
    
    async def purge_completed_jobs(self, days_old: int = 30) -> int:
        """Purge completed jobs older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Scan for old completed jobs
            response = self.jobs_table.scan(
                FilterExpression="#status IN (:completed, :failed) AND processing_completed_at < :cutoff",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':completed': JobStatus.COMPLETED.value,
                    ':failed': JobStatus.FAILED.value,
                    ':cutoff': cutoff_date.isoformat()
                }
            )
            
            # Delete old jobs
            deleted_count = 0
            for item in response['Items']:
                self.jobs_table.delete_item(Key={'job_id': item['job_id']})
                deleted_count += 1
            
            logger.info(f"Purged {deleted_count} completed jobs older than {days_old} days")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error purging completed jobs: {str(e)}")
            return 0