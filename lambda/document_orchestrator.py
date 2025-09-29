"""
Document Processing Orchestrator Lambda Function

This Lambda function handles document processing orchestration through EventBridge.
It receives events from API Gateway, S3, and DynamoDB to coordinate document processing workflows.
"""

import json
import boto3
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS services
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
eventbridge = boto3.client('events')
textract = boto3.client('textract')
bedrock = boto3.client('bedrock-runtime')

# Environment variables
DOCUMENT_JOBS_TABLE = os.environ.get('DOCUMENT_JOBS_TABLE', 'document-jobs')
APPROVAL_TABLE = os.environ.get('APPROVAL_TABLE', 'document-approvals')
S3_BUCKET = os.environ.get('S3_BUCKET', 'emergency-docs-bucket-us-east-1')
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'emergency-docs-events')

def lambda_handler(event, context):
    """
    Main Lambda handler for document processing orchestration
    """
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Determine event source and route accordingly
        event_source = event.get('source', 'unknown')
        detail_type = event.get('detail-type', 'unknown')
        
        if event_source == 'aws.s3':
            return handle_s3_event(event, context)
        elif event_source == 'aws.dynamodb':
            return handle_dynamodb_event(event, context)
        elif event_source == 'emergency.docs':
            return handle_custom_event(event, context)
        elif 'httpMethod' in event:
            return handle_api_gateway_event(event, context)
        else:
            return handle_eventbridge_event(event, context)
            
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'event_id': context.aws_request_id
            })
        }

def handle_s3_event(event, context):
    """Handle S3 bucket events (file uploads, deletions)"""
    try:
        records = event.get('Records', [])
        results = []
        
        for record in records:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            event_name = record['eventName']
            
            logger.info(f"S3 Event: {event_name} for {bucket}/{key}")
            
            if event_name.startswith('ObjectCreated'):
                result = handle_document_upload(bucket, key)
                results.append(result)
            elif event_name.startswith('ObjectRemoved'):
                result = handle_document_deletion(bucket, key)
                results.append(result)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'S3 events processed',
                'results': results
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling S3 event: {str(e)}")
        raise

def handle_document_upload(bucket, key):
    """Process new document upload"""
    try:
        # Check if this is a document we should process
        if not (key.endswith('.pdf') or key.endswith('.md')):
            return {'action': 'skipped', 'reason': 'not a processable document'}
        
        # Extract metadata from S3 object
        response = s3_client.head_object(Bucket=bucket, Key=key)
        metadata = response.get('Metadata', {})
        
        # Create processing event
        processing_event = {
            'source': 'emergency.docs',
            'detail-type': 'Document Upload Detected',
            'detail': {
                'bucket': bucket,
                'key': key,
                'size': response.get('ContentLength', 0),
                'metadata': metadata,
                'timestamp': datetime.utcnow().isoformat(),
                'processing_required': True
            }
        }
        
        # Send event to EventBridge
        send_event_to_bridge(processing_event)
        
        return {
            'action': 'processed',
            'bucket': bucket,
            'key': key,
            'event_sent': True
        }
        
    except Exception as e:
        logger.error(f"Error processing document upload {bucket}/{key}: {str(e)}")
        return {'action': 'failed', 'error': str(e)}

def handle_dynamodb_event(event, context):
    """Handle DynamoDB stream events (job status changes)"""
    try:
        records = event.get('Records', [])
        results = []
        
        for record in records:
            event_name = record['eventName']
            table_name = record['dynamodb'].get('Keys', {}).get('job_id', {}).get('S', 'unknown')
            
            logger.info(f"DynamoDB Event: {event_name} for job {table_name}")
            
            if event_name == 'INSERT':
                result = handle_job_created(record)
            elif event_name == 'MODIFY':
                result = handle_job_updated(record)
            elif event_name == 'REMOVE':
                result = handle_job_deleted(record)
            else:
                result = {'action': 'ignored', 'event': event_name}
            
            results.append(result)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'DynamoDB events processed',
                'results': results
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling DynamoDB event: {str(e)}")
        raise

def handle_job_created(record):
    """Handle new job creation"""
    try:
        # Extract job data from DynamoDB record
        new_image = record['dynamodb'].get('NewImage', {})
        job_id = new_image.get('job_id', {}).get('S', '')
        status = new_image.get('status', {}).get('S', '')
        user_id = new_image.get('user_id', {}).get('S', '')
        
        # Create job creation event
        job_event = {
            'source': 'emergency.docs',
            'detail-type': 'Job Created',
            'detail': {
                'job_id': job_id,
                'status': status,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'job_created'
            }
        }
        
        # Send to EventBridge
        send_event_to_bridge(job_event)
        
        # If job requires approval, trigger approval workflow
        if status == 'pending_approval':
            trigger_approval_workflow(job_id, user_id)
        
        return {
            'action': 'job_created_event_sent',
            'job_id': job_id,
            'status': status
        }
        
    except Exception as e:
        logger.error(f"Error handling job creation: {str(e)}")
        return {'action': 'failed', 'error': str(e)}

def handle_job_updated(record):
    """Handle job status updates"""
    try:
        old_image = record['dynamodb'].get('OldImage', {})
        new_image = record['dynamodb'].get('NewImage', {})
        
        job_id = new_image.get('job_id', {}).get('S', '')
        old_status = old_image.get('status', {}).get('S', '')
        new_status = new_image.get('status', {}).get('S', '')
        
        # Only process if status actually changed
        if old_status != new_status:
            # Create status change event
            status_event = {
                'source': 'emergency.docs',
                'detail-type': 'Job Status Changed',
                'detail': {
                    'job_id': job_id,
                    'old_status': old_status,
                    'new_status': new_status,
                    'timestamp': datetime.utcnow().isoformat(),
                    'action': 'status_changed'
                }
            }
            
            # Send to EventBridge
            send_event_to_bridge(status_event)
            
            # Handle specific status transitions
            if new_status == 'approved':
                trigger_document_processing(job_id)
            elif new_status == 'completed':
                send_completion_notification(job_id)
            elif new_status == 'failed':
                send_failure_notification(job_id)
        
        return {
            'action': 'status_change_processed',
            'job_id': job_id,
            'status_change': f"{old_status} -> {new_status}"
        }
        
    except Exception as e:
        logger.error(f"Error handling job update: {str(e)}")
        return {'action': 'failed', 'error': str(e)}

def handle_job_deleted(record):
    """Handle job deletion"""
    try:
        old_image = record['dynamodb'].get('OldImage', {})
        job_id = old_image.get('job_id', {}).get('S', '')
        
        # Create job deletion event
        deletion_event = {
            'source': 'emergency.docs',
            'detail-type': 'Job Deleted',
            'detail': {
                'job_id': job_id,
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'job_deleted'
            }
        }
        
        # Send to EventBridge
        send_event_to_bridge(deletion_event)
        
        return {
            'action': 'job_deletion_processed',
            'job_id': job_id
        }
        
    except Exception as e:
        logger.error(f"Error handling job deletion: {str(e)}")
        return {'action': 'failed', 'error': str(e)}

def handle_custom_event(event, context):
    """Handle custom events from our application"""
    try:
        detail_type = event.get('detail-type', '')
        detail = event.get('detail', {})
        
        logger.info(f"Custom event: {detail_type}")
        
        if detail_type == 'Document Processing Required':
            return handle_processing_request(detail)
        elif detail_type == 'Approval Required':
            return handle_approval_event(detail)
        elif detail_type == 'User Activity':
            return handle_user_activity(detail)
        else:
            logger.warning(f"Unknown custom event type: {detail_type}")
            return {'action': 'ignored', 'reason': 'unknown event type'}
            
    except Exception as e:
        logger.error(f"Error handling custom event: {str(e)}")
        raise

def handle_approval_event(detail):
    """Handle approval workflow events"""
    try:
        job_id = detail.get('job_id')
        user_id = detail.get('user_id')
        action = detail.get('action', '')
        
        logger.info(f"Approval event: {action} for job {job_id}")
        
        if action == 'approval_required':
            # Handle approval requirement
            return {
                'action': 'approval_workflow_triggered',
                'job_id': job_id,
                'user_id': user_id
            }
        elif action == 'approved':
            # Handle approval granted
            trigger_document_processing(job_id)
            return {
                'action': 'processing_triggered_after_approval',
                'job_id': job_id
            }
        elif action == 'rejected':
            # Handle approval rejection
            return {
                'action': 'approval_rejected_processed',
                'job_id': job_id
            }
        else:
            return {
                'action': 'unknown_approval_action',
                'provided_action': action
            }
            
    except Exception as e:
        logger.error(f"Error handling approval event: {str(e)}")
        return {'action': 'failed', 'error': str(e)}

def handle_processing_request(detail):
    """Handle document processing requests"""
    try:
        job_id = detail.get('job_id')
        files = detail.get('files', [])
        urls = detail.get('urls', [])
        
        # Create processing tasks
        processing_tasks = []
        
        for file_info in files:
            task = {
                'type': 'file',
                'job_id': job_id,
                'filename': file_info.get('filename'),
                'size': file_info.get('size'),
                'content_type': file_info.get('content_type')
            }
            processing_tasks.append(task)
        
        for url in urls:
            task = {
                'type': 'url',
                'job_id': job_id,
                'url': url
            }
            processing_tasks.append(task)
        
        # Send individual processing events
        for task in processing_tasks:
            task_event = {
                'source': 'emergency.docs',
                'detail-type': 'Process Document Task',
                'detail': {
                    **task,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            send_event_to_bridge(task_event)
        
        return {
            'action': 'processing_tasks_created',
            'job_id': job_id,
            'task_count': len(processing_tasks)
        }
        
    except Exception as e:
        logger.error(f"Error handling processing request: {str(e)}")
        return {'action': 'failed', 'error': str(e)}

def trigger_approval_workflow(job_id, user_id):
    """Trigger approval workflow for a job"""
    try:
        # Create approval required event
        approval_event = {
            'source': 'emergency.docs',
            'detail-type': 'Approval Required',
            'detail': {
                'job_id': job_id,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'deadline': (datetime.utcnow() + timedelta(days=7)).isoformat(),
                'action': 'approval_required'
            }
        }
        
        send_event_to_bridge(approval_event)
        logger.info(f"Approval workflow triggered for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error triggering approval workflow: {str(e)}")

def trigger_document_processing(job_id):
    """Trigger actual document processing after approval"""
    try:
        # Get job details from DynamoDB
        table = dynamodb.Table(DOCUMENT_JOBS_TABLE)
        response = table.get_item(Key={'job_id': job_id})
        
        if 'Item' not in response:
            raise Exception(f"Job {job_id} not found")
        
        job = response['Item']
        
        # Create processing event
        processing_event = {
            'source': 'emergency.docs',
            'detail-type': 'Start Document Processing',
            'detail': {
                'job_id': job_id,
                'user_id': job.get('user_id'),
                'files': job.get('files', []),
                'urls': job.get('urls', []),
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'start_processing'
            }
        }
        
        send_event_to_bridge(processing_event)
        logger.info(f"Document processing triggered for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error triggering document processing: {str(e)}")

def send_completion_notification(job_id):
    """Send job completion notification"""
    try:
        completion_event = {
            'source': 'emergency.docs',
            'detail-type': 'Job Completed',
            'detail': {
                'job_id': job_id,
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'job_completed'
            }
        }
        
        send_event_to_bridge(completion_event)
        logger.info(f"Completion notification sent for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error sending completion notification: {str(e)}")

def send_failure_notification(job_id):
    """Send job failure notification"""
    try:
        failure_event = {
            'source': 'emergency.docs',
            'detail-type': 'Job Failed',
            'detail': {
                'job_id': job_id,
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'job_failed'
            }
        }
        
        send_event_to_bridge(failure_event)
        logger.info(f"Failure notification sent for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error sending failure notification: {str(e)}")

def send_event_to_bridge(event_data):
    """Send event to EventBridge"""
    try:
        response = eventbridge.put_events(
            Entries=[
                {
                    'Source': event_data.get('source', 'emergency.docs'),
                    'DetailType': event_data.get('detail-type', 'Custom Event'),
                    'Detail': json.dumps(event_data.get('detail', {})),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        
        logger.info(f"Event sent to EventBridge: {event_data.get('detail-type')}")
        return response
        
    except Exception as e:
        logger.error(f"Error sending event to EventBridge: {str(e)}")
        raise

def handle_api_gateway_event(event, context):
    """Handle direct API Gateway invocations"""
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        if http_method == 'POST' and path == '/orchestrate':
            body = json.loads(event.get('body', '{}'))
            action = body.get('action', '')
            
            if action == 'process_documents':
                return handle_processing_request(body)
            elif action == 'trigger_approval':
                job_id = body.get('job_id')
                user_id = body.get('user_id')
                trigger_approval_workflow(job_id, user_id)
                return {
                    'statusCode': 200,
                    'body': json.dumps({'message': 'Approval workflow triggered'})
                }
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Unknown action'})
                }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Endpoint not found'})
            }
            
    except Exception as e:
        logger.error(f"Error handling API Gateway event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handle_eventbridge_event(event, context):
    """Handle EventBridge scheduled events"""
    try:
        # This could handle scheduled maintenance, cleanup, monitoring, etc.
        detail_type = event.get('detail-type', '')
        
        if detail_type == 'Scheduled Event':
            detail = event.get('detail', {})
            schedule_type = detail.get('schedule_type', '')
            
            if schedule_type == 'cleanup':
                return handle_cleanup_task()
            elif schedule_type == 'monitoring':
                return handle_monitoring_task()
            else:
                return {'action': 'ignored', 'reason': 'unknown schedule type'}
        
        return {'action': 'processed', 'detail_type': detail_type}
        
    except Exception as e:
        logger.error(f"Error handling EventBridge event: {str(e)}")
        raise

def handle_cleanup_task():
    """Handle scheduled cleanup tasks"""
    try:
        # Clean up old jobs, expired approvals, etc.
        cleanup_results = {
            'expired_approvals_cleaned': 0,
            'old_jobs_archived': 0,
            'temp_files_removed': 0
        }
        
        # TODO: Implement actual cleanup logic
        logger.info("Cleanup task completed")
        return {'action': 'cleanup_completed', 'results': cleanup_results}
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")
        return {'action': 'cleanup_failed', 'error': str(e)}

def handle_monitoring_task():
    """Handle scheduled monitoring tasks"""
    try:
        # Monitor system health, send alerts, etc.
        monitoring_results = {
            'system_health': 'healthy',
            'active_jobs': 0,
            'pending_approvals': 0,
            'storage_usage': '0%'
        }
        
        # TODO: Implement actual monitoring logic
        logger.info("Monitoring task completed")
        return {'action': 'monitoring_completed', 'results': monitoring_results}
        
    except Exception as e:
        logger.error(f"Error in monitoring task: {str(e)}")
        return {'action': 'monitoring_failed', 'error': str(e)}

def handle_user_activity(detail):
    """Handle user activity events for analytics"""
    try:
        user_id = detail.get('user_id')
        activity_type = detail.get('activity_type')
        metadata = detail.get('metadata', {})
        
        # Store activity for analytics (could integrate with existing user tracking)
        logger.info(f"User activity recorded: {user_id} - {activity_type}")
        
        return {
            'action': 'activity_recorded',
            'user_id': user_id,
            'activity_type': activity_type
        }
        
    except Exception as e:
        logger.error(f"Error handling user activity: {str(e)}")
        return {'action': 'failed', 'error': str(e)}

def handle_document_deletion(bucket, key):
    """Handle document deletion from S3"""
    try:
        # Create deletion event
        deletion_event = {
            'source': 'emergency.docs',
            'detail-type': 'Document Deleted',
            'detail': {
                'bucket': bucket,
                'key': key,
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'document_deleted'
            }
        }
        
        send_event_to_bridge(deletion_event)
        
        return {
            'action': 'deletion_processed',
            'bucket': bucket,
            'key': key
        }
        
    except Exception as e:
        logger.error(f"Error processing document deletion {bucket}/{key}: {str(e)}")
        return {'action': 'failed', 'error': str(e)}