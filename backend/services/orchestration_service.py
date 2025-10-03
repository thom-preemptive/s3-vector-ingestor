"""
EventBridge Integration Service

This service integrates the FastAPI application with the serverless orchestration layer.
It sends events to EventBridge for async processing and handles event-driven workflows.
"""

import boto3
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class EventBridgeService:
    def __init__(self, region_name='us-east-1'):
        self.events_client = boto3.client('events', region_name=region_name)
        self.event_bus_name = os.environ.get('EVENT_BUS_NAME', 'emergency-docs-events-dev')
        self.region = region_name
    
    async def send_document_processing_event(self, 
                                           job_id: str, 
                                           user_id: str, 
                                           files: List[Dict[str, Any]] = None, 
                                           urls: List[str] = None,
                                           job_name: str = None) -> bool:
        """Send document processing event to EventBridge"""
        try:
            event_detail = {
                'job_id': job_id,
                'user_id': user_id,
                'job_name': job_name or f'Job {job_id}',
                'files': files or [],
                'urls': urls or [],
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'process_documents'
            }
            
            response = self.events_client.put_events(
                Entries=[
                    {
                        'Source': 'agent2.ingestor',
                        'DetailType': 'Document Processing Required',
                        'Detail': json.dumps(event_detail),
                        'EventBusName': self.event_bus_name
                    }
                ]
            )
            
            if response['FailedEntryCount'] == 0:
                logger.info(f"Document processing event sent for job {job_id}")
                return True
            else:
                logger.error(f"Failed to send processing event: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending document processing event: {str(e)}")
            return False
    
    async def send_approval_event(self, 
                                job_id: str, 
                                user_id: str, 
                                action: str, 
                                approval_id: str = None,
                                approver_id: str = None,
                                comment: str = None) -> bool:
        """Send approval workflow event to EventBridge"""
        try:
            event_detail = {
                'job_id': job_id,
                'user_id': user_id,
                'action': action,  # 'approval_required', 'approved', 'rejected'
                'approval_id': approval_id,
                'approver_id': approver_id,
                'comment': comment,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            response = self.events_client.put_events(
                Entries=[
                    {
                        'Source': 'emergency.docs',
                        'DetailType': 'Approval Workflow Event',
                        'Detail': json.dumps(event_detail),
                        'EventBusName': self.event_bus_name
                    }
                ]
            )
            
            if response['FailedEntryCount'] == 0:
                logger.info(f"Approval event sent: {action} for job {job_id}")
                return True
            else:
                logger.error(f"Failed to send approval event: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending approval event: {str(e)}")
            return False
    
    async def send_user_activity_event(self, 
                                     user_id: str, 
                                     activity_type: str, 
                                     metadata: Dict[str, Any] = None) -> bool:
        """Send user activity event to EventBridge"""
        try:
            event_detail = {
                'user_id': user_id,
                'activity_type': activity_type,
                'metadata': metadata or {},
                'timestamp': datetime.utcnow().isoformat()
            }
            
            response = self.events_client.put_events(
                Entries=[
                    {
                        'Source': 'emergency.docs',
                        'DetailType': 'User Activity',
                        'Detail': json.dumps(event_detail),
                        'EventBusName': self.event_bus_name
                    }
                ]
            )
            
            if response['FailedEntryCount'] == 0:
                logger.info(f"User activity event sent: {activity_type} for {user_id}")
                return True
            else:
                logger.error(f"Failed to send user activity event: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending user activity event: {str(e)}")
            return False
    
    async def send_job_status_event(self, 
                                  job_id: str, 
                                  old_status: str, 
                                  new_status: str, 
                                  user_id: str = None,
                                  metadata: Dict[str, Any] = None) -> bool:
        """Send job status change event to EventBridge"""
        try:
            event_detail = {
                'job_id': job_id,
                'old_status': old_status,
                'new_status': new_status,
                'user_id': user_id,
                'metadata': metadata or {},
                'timestamp': datetime.utcnow().isoformat()
            }
            
            response = self.events_client.put_events(
                Entries=[
                    {
                        'Source': 'emergency.docs',
                        'DetailType': 'Job Status Changed',
                        'Detail': json.dumps(event_detail),
                        'EventBusName': self.event_bus_name
                    }
                ]
            )
            
            if response['FailedEntryCount'] == 0:
                logger.info(f"Job status event sent: {job_id} {old_status} -> {new_status}")
                return True
            else:
                logger.error(f"Failed to send job status event: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending job status event: {str(e)}")
            return False
    
    async def send_system_event(self, 
                              event_type: str, 
                              detail: Dict[str, Any]) -> bool:
        """Send general system event to EventBridge"""
        try:
            event_detail = {
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                **detail
            }
            
            response = self.events_client.put_events(
                Entries=[
                    {
                        'Source': 'emergency.docs',
                        'DetailType': f'System {event_type.replace("_", " ").title()}',
                        'Detail': json.dumps(event_detail),
                        'EventBusName': self.event_bus_name
                    }
                ]
            )
            
            if response['FailedEntryCount'] == 0:
                logger.info(f"System event sent: {event_type}")
                return True
            else:
                logger.error(f"Failed to send system event: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending system event: {str(e)}")
            return False
    
    async def trigger_document_processing(self, 
                                        job_id: str, 
                                        files: List[Dict[str, Any]] = None, 
                                        urls: List[str] = None) -> bool:
        """Trigger individual document processing tasks"""
        try:
            success_count = 0
            total_tasks = 0
            
            # Create file processing tasks
            if files:
                for file_info in files:
                    total_tasks += 1
                    task_detail = {
                        'type': 'file',
                        'job_id': job_id,
                        'filename': file_info.get('filename'),
                        'size': file_info.get('size'),
                        'content_type': file_info.get('content_type'),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    response = self.events_client.put_events(
                        Entries=[
                            {
                                'Source': 'emergency.docs',
                                'DetailType': 'Process Document Task',
                                'Detail': json.dumps(task_detail),
                                'EventBusName': self.event_bus_name
                            }
                        ]
                    )
                    
                    if response['FailedEntryCount'] == 0:
                        success_count += 1
                    else:
                        logger.error(f"Failed to send file processing task: {file_info.get('filename')}")
            
            # Create URL processing tasks
            if urls:
                for url in urls:
                    total_tasks += 1
                    task_detail = {
                        'type': 'url',
                        'job_id': job_id,
                        'url': url,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    response = self.events_client.put_events(
                        Entries=[
                            {
                                'Source': 'emergency.docs',
                                'DetailType': 'Process Document Task',
                                'Detail': json.dumps(task_detail),
                                'EventBusName': self.event_bus_name
                            }
                        ]
                    )
                    
                    if response['FailedEntryCount'] == 0:
                        success_count += 1
                    else:
                        logger.error(f"Failed to send URL processing task: {url}")
            
            logger.info(f"Triggered {success_count}/{total_tasks} processing tasks for job {job_id}")
            return success_count == total_tasks
            
        except Exception as e:
            logger.error(f"Error triggering document processing: {str(e)}")
            return False
    
    async def get_event_bus_info(self) -> Dict[str, Any]:
        """Get information about the event bus"""
        try:
            response = self.events_client.describe_event_bus(Name=self.event_bus_name)
            
            # Get rules for this event bus
            rules_response = self.events_client.list_rules(EventBusName=self.event_bus_name)
            rules = rules_response.get('Rules', [])
            
            return {
                'event_bus': response,
                'rules_count': len(rules),
                'rules': [
                    {
                        'name': rule['Name'],
                        'state': rule['State'],
                        'description': rule.get('Description', '')
                    }
                    for rule in rules
                ],
                'status': 'active'
            }
            
        except Exception as e:
            logger.error(f"Error getting event bus info: {str(e)}")
            return {
                'event_bus': None,
                'rules_count': 0,
                'rules': [],
                'status': 'error',
                'error': str(e)
            }
    
    async def test_event_bus_connection(self) -> bool:
        """Test connection to EventBridge"""
        try:
            # Send a test event
            test_event = {
                'test': True,
                'timestamp': datetime.utcnow().isoformat(),
                'message': 'EventBridge connection test'
            }
            
            response = self.events_client.put_events(
                Entries=[
                    {
                        'Source': 'emergency.docs',
                        'DetailType': 'Connection Test',
                        'Detail': json.dumps(test_event),
                        'EventBusName': self.event_bus_name
                    }
                ]
            )
            
            if response['FailedEntryCount'] == 0:
                logger.info("EventBridge connection test successful")
                return True
            else:
                logger.error(f"EventBridge connection test failed: {response}")
                return False
                
        except Exception as e:
            logger.error(f"EventBridge connection test error: {str(e)}")
            return False

class OrchestrationService:
    """Service to coordinate between FastAPI app and serverless orchestration"""
    
    def __init__(self):
        self.eventbridge = EventBridgeService()
    
    async def orchestrate_document_processing(self, 
                                            job_id: str, 
                                            user_id: str, 
                                            files: List[Dict[str, Any]] = None, 
                                            urls: List[str] = None,
                                            job_name: str = None,
                                            approval_required: bool = False) -> Dict[str, Any]:
        """Orchestrate document processing workflow"""
        try:
            if approval_required:
                # Send approval required event
                approval_sent = await self.eventbridge.send_approval_event(
                    job_id=job_id,
                    user_id=user_id,
                    action='approval_required'
                )
                
                if approval_sent:
                    return {
                        'status': 'approval_required',
                        'job_id': job_id,
                        'message': 'Approval request sent to orchestration layer'
                    }
                else:
                    raise Exception("Failed to send approval request event")
            else:
                # Send processing event directly
                processing_sent = await self.eventbridge.send_document_processing_event(
                    job_id=job_id,
                    user_id=user_id,
                    files=files,
                    urls=urls,
                    job_name=job_name
                )
                
                if processing_sent:
                    return {
                        'status': 'processing_initiated',
                        'job_id': job_id,
                        'message': 'Document processing initiated through orchestration layer'
                    }
                else:
                    raise Exception("Failed to send processing event")
                    
        except Exception as e:
            logger.error(f"Error orchestrating document processing: {str(e)}")
            return {
                'status': 'error',
                'job_id': job_id,
                'error': str(e)
            }
    
    async def handle_approval_decision(self, 
                                     job_id: str, 
                                     approval_id: str, 
                                     decision: str, 
                                     approver_id: str, 
                                     comment: str = None) -> Dict[str, Any]:
        """Handle approval decision through orchestration"""
        try:
            # Send approval decision event
            decision_sent = await self.eventbridge.send_approval_event(
                job_id=job_id,
                user_id=approver_id,
                action=decision,  # 'approved' or 'rejected'
                approval_id=approval_id,
                approver_id=approver_id,
                comment=comment
            )
            
            if decision_sent:
                return {
                    'status': 'decision_processed',
                    'job_id': job_id,
                    'approval_id': approval_id,
                    'decision': decision,
                    'message': f'Approval {decision} sent to orchestration layer'
                }
            else:
                raise Exception("Failed to send approval decision event")
                
        except Exception as e:
            logger.error(f"Error handling approval decision: {str(e)}")
            return {
                'status': 'error',
                'job_id': job_id,
                'error': str(e)
            }
    
    async def track_user_activity(self, 
                                user_id: str, 
                                activity_type: str, 
                                metadata: Dict[str, Any] = None) -> bool:
        """Track user activity through orchestration"""
        try:
            return await self.eventbridge.send_user_activity_event(
                user_id=user_id,
                activity_type=activity_type,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error tracking user activity: {str(e)}")
            return False
    
    async def notify_job_status_change(self, 
                                     job_id: str, 
                                     old_status: str, 
                                     new_status: str, 
                                     user_id: str = None,
                                     metadata: Dict[str, Any] = None) -> bool:
        """Notify orchestration layer of job status changes"""
        try:
            return await self.eventbridge.send_job_status_event(
                job_id=job_id,
                old_status=old_status,
                new_status=new_status,
                user_id=user_id,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error notifying job status change: {str(e)}")
            return False
    
    async def get_orchestration_status(self) -> Dict[str, Any]:
        """Get status of the orchestration infrastructure"""
        try:
            eventbridge_info = await self.eventbridge.get_event_bus_info()
            connection_test = await self.eventbridge.test_event_bus_connection()
            
            return {
                'status': 'healthy' if connection_test else 'unhealthy',
                'eventbridge': eventbridge_info,
                'connection_test': connection_test,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting orchestration status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }