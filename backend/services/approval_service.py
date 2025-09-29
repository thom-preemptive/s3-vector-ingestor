import boto3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import os
from enum import Enum

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class UserRole(Enum):
    USER = "user"
    APPROVER = "approver"
    ADMIN = "admin"

class ApprovalService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.approval_table_name = os.getenv('APPROVAL_TABLE', 'document-approvals')
        self.user_tracking_table_name = os.getenv('USER_TRACKING_TABLE', 'user-tracking')
        
        # Create tables if they don't exist
        self.approval_table = self._get_or_create_approval_table()
        self.user_tracking_table = self._get_or_create_user_tracking_table()
    
    def _get_or_create_approval_table(self):
        """Get or create the approval workflow table"""
        try:
            table = self.dynamodb.Table(self.approval_table_name)
            table.load()  # Test if table exists
            return table
        except:
            # Table doesn't exist, create it
            return self._create_approval_table()
    
    def _create_approval_table(self):
        """Create approval workflow table"""
        table = self.dynamodb.create_table(
            TableName=self.approval_table_name,
            KeySchema=[
                {'AttributeName': 'approval_id', 'KeyType': 'HASH'},
            ],
            AttributeDefinitions=[
                {'AttributeName': 'approval_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'status', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'},
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserIdIndex',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'StatusIndex',
                    'KeySchema': [
                        {'AttributeName': 'status', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for table to be created
        table.wait_until_exists()
        return table
    
    def _get_or_create_user_tracking_table(self):
        """Get or create the user tracking table"""
        try:
            table = self.dynamodb.Table(self.user_tracking_table_name)
            table.load()  # Test if table exists
            return table
        except:
            # Table doesn't exist, create it
            return self._create_user_tracking_table()
    
    def _create_user_tracking_table(self):
        """Create user tracking table"""
        table = self.dynamodb.create_table(
            TableName=self.user_tracking_table_name,
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'last_activity', 'AttributeType': 'S'},
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'LastActivityIndex',
                    'KeySchema': [
                        {'AttributeName': 'last_activity', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for table to be created
        table.wait_until_exists()
        return table
    
    async def create_approval_request(self, 
                                    job_id: str, 
                                    user_id: str, 
                                    document_list: List[Dict[str, Any]], 
                                    request_reason: str = None,
                                    approval_deadline: datetime = None) -> str:
        """Create a new approval request"""
        try:
            approval_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            # Default deadline is 7 days if not specified
            if not approval_deadline:
                approval_deadline = current_time + timedelta(days=7)
            
            approval_request = {
                'approval_id': approval_id,
                'job_id': job_id,
                'user_id': user_id,
                'status': ApprovalStatus.PENDING.value,
                'created_at': current_time.isoformat(),
                'updated_at': current_time.isoformat(),
                'deadline': approval_deadline.isoformat(),
                'request_reason': request_reason or "Document processing approval",
                'document_count': len(document_list),
                'documents': document_list,
                'approver_id': None,
                'approval_comment': None,
                'approval_timestamp': None,
                'metadata': {
                    'total_documents': len(document_list),
                    'document_types': list(set(doc.get('type', 'unknown') for doc in document_list)),
                    'estimated_processing_time': len(document_list) * 30,  # 30 seconds per document estimate
                    'priority': 'normal'
                }
            }
            
            self.approval_table.put_item(Item=approval_request)
            
            # Track user activity
            await self.track_user_activity(user_id, 'approval_request_created', {
                'approval_id': approval_id,
                'document_count': len(document_list)
            })
            
            return approval_id
            
        except Exception as e:
            raise Exception(f"Failed to create approval request: {str(e)}")
    
    async def approve_request(self, 
                            approval_id: str, 
                            approver_id: str, 
                            comment: str = None) -> Dict[str, Any]:
        """Approve a pending request"""
        try:
            current_time = datetime.utcnow()
            
            # Get current approval request
            response = self.approval_table.get_item(Key={'approval_id': approval_id})
            if 'Item' not in response:
                raise Exception("Approval request not found")
            
            approval_request = response['Item']
            
            # Check if still pending
            if approval_request['status'] != ApprovalStatus.PENDING.value:
                raise Exception(f"Request is already {approval_request['status']}")
            
            # Check if expired
            deadline = datetime.fromisoformat(approval_request['deadline'])
            if current_time > deadline:
                await self._expire_request(approval_id)
                raise Exception("Approval request has expired")
            
            # Update approval request
            self.approval_table.update_item(
                Key={'approval_id': approval_id},
                UpdateExpression="""
                    SET #status = :status, 
                        updated_at = :updated, 
                        approver_id = :approver, 
                        approval_comment = :comment, 
                        approval_timestamp = :timestamp
                """,
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': ApprovalStatus.APPROVED.value,
                    ':updated': current_time.isoformat(),
                    ':approver': approver_id,
                    ':comment': comment or "Approved",
                    ':timestamp': current_time.isoformat()
                }
            )
            
            # Track activities
            await self.track_user_activity(approver_id, 'approval_granted', {
                'approval_id': approval_id,
                'original_user': approval_request['user_id']
            })
            
            await self.track_user_activity(approval_request['user_id'], 'approval_received', {
                'approval_id': approval_id,
                'approver': approver_id
            })
            
            return {
                'approval_id': approval_id,
                'status': ApprovalStatus.APPROVED.value,
                'approved_by': approver_id,
                'approved_at': current_time.isoformat(),
                'job_id': approval_request['job_id']
            }
            
        except Exception as e:
            raise Exception(f"Failed to approve request: {str(e)}")
    
    async def reject_request(self, 
                           approval_id: str, 
                           approver_id: str, 
                           reason: str) -> Dict[str, Any]:
        """Reject a pending request"""
        try:
            current_time = datetime.utcnow()
            
            # Get current approval request
            response = self.approval_table.get_item(Key={'approval_id': approval_id})
            if 'Item' not in response:
                raise Exception("Approval request not found")
            
            approval_request = response['Item']
            
            # Check if still pending
            if approval_request['status'] != ApprovalStatus.PENDING.value:
                raise Exception(f"Request is already {approval_request['status']}")
            
            # Update approval request
            self.approval_table.update_item(
                Key={'approval_id': approval_id},
                UpdateExpression="""
                    SET #status = :status, 
                        updated_at = :updated, 
                        approver_id = :approver, 
                        approval_comment = :reason, 
                        approval_timestamp = :timestamp
                """,
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': ApprovalStatus.REJECTED.value,
                    ':updated': current_time.isoformat(),
                    ':approver': approver_id,
                    ':reason': reason,
                    ':timestamp': current_time.isoformat()
                }
            )
            
            # Track activities
            await self.track_user_activity(approver_id, 'approval_rejected', {
                'approval_id': approval_id,
                'original_user': approval_request['user_id'],
                'reason': reason
            })
            
            await self.track_user_activity(approval_request['user_id'], 'approval_denied', {
                'approval_id': approval_id,
                'approver': approver_id,
                'reason': reason
            })
            
            return {
                'approval_id': approval_id,
                'status': ApprovalStatus.REJECTED.value,
                'rejected_by': approver_id,
                'rejected_at': current_time.isoformat(),
                'reason': reason
            }
            
        except Exception as e:
            raise Exception(f"Failed to reject request: {str(e)}")
    
    async def _expire_request(self, approval_id: str) -> None:
        """Mark a request as expired"""
        current_time = datetime.utcnow()
        
        self.approval_table.update_item(
            Key={'approval_id': approval_id},
            UpdateExpression="SET #status = :status, updated_at = :updated",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': ApprovalStatus.EXPIRED.value,
                ':updated': current_time.isoformat()
            }
        )
    
    async def get_pending_approvals(self, approver_id: str = None) -> List[Dict[str, Any]]:
        """Get all pending approval requests"""
        try:
            response = self.approval_table.query(
                IndexName='StatusIndex',
                KeyConditionExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': ApprovalStatus.PENDING.value},
                ScanIndexForward=False  # Most recent first
            )
            
            pending_approvals = response.get('Items', [])
            
            # Check for expired requests and update them
            current_time = datetime.utcnow()
            valid_approvals = []
            
            for approval in pending_approvals:
                deadline = datetime.fromisoformat(approval['deadline'])
                if current_time > deadline:
                    await self._expire_request(approval['approval_id'])
                else:
                    valid_approvals.append(approval)
            
            return valid_approvals
            
        except Exception as e:
            raise Exception(f"Failed to get pending approvals: {str(e)}")
    
    async def get_user_approval_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get approval history for a user"""
        try:
            response = self.approval_table.query(
                IndexName='UserIdIndex',
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id},
                ScanIndexForward=False  # Most recent first
            )
            
            return response.get('Items', [])
            
        except Exception as e:
            raise Exception(f"Failed to get user approval history: {str(e)}")
    
    async def track_user_activity(self, 
                                user_id: str, 
                                activity_type: str, 
                                metadata: Dict[str, Any] = None) -> None:
        """Track user activity for analytics and auditing"""
        try:
            current_time = datetime.utcnow()
            
            # Get or create user tracking record
            try:
                response = self.user_tracking_table.get_item(Key={'user_id': user_id})
                user_record = response.get('Item', {})
            except:
                user_record = {}
            
            # Initialize user record if new
            if not user_record:
                user_record = {
                    'user_id': user_id,
                    'created_at': current_time.isoformat(),
                    'total_activities': 0,
                    'activity_types': {},
                    'recent_activities': []
                }
            
            # Update activity counters
            user_record['total_activities'] = user_record.get('total_activities', 0) + 1
            user_record['last_activity'] = current_time.isoformat()
            
            activity_types = user_record.get('activity_types', {})
            activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
            user_record['activity_types'] = activity_types
            
            # Add to recent activities (keep last 50)
            activity_entry = {
                'timestamp': current_time.isoformat(),
                'type': activity_type,
                'metadata': metadata or {}
            }
            
            recent_activities = user_record.get('recent_activities', [])
            recent_activities.insert(0, activity_entry)
            user_record['recent_activities'] = recent_activities[:50]  # Keep only last 50
            
            # Save updated record
            self.user_tracking_table.put_item(Item=user_record)
            
        except Exception as e:
            print(f"Warning: Failed to track user activity: {str(e)}")
            # Don't raise exception for tracking failures
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        try:
            # Get user tracking data
            response = self.user_tracking_table.get_item(Key={'user_id': user_id})
            user_record = response.get('Item', {})
            
            if not user_record:
                return {
                    'user_id': user_id,
                    'total_activities': 0,
                    'activity_types': {},
                    'recent_activities': [],
                    'approval_statistics': {
                        'total_requests': 0,
                        'approved': 0,
                        'rejected': 0,
                        'pending': 0,
                        'expired': 0
                    }
                }
            
            # Get approval statistics
            approval_history = await self.get_user_approval_history(user_id)
            approval_stats = {
                'total_requests': len(approval_history),
                'approved': len([a for a in approval_history if a['status'] == ApprovalStatus.APPROVED.value]),
                'rejected': len([a for a in approval_history if a['status'] == ApprovalStatus.REJECTED.value]),
                'pending': len([a for a in approval_history if a['status'] == ApprovalStatus.PENDING.value]),
                'expired': len([a for a in approval_history if a['status'] == ApprovalStatus.EXPIRED.value])
            }
            
            user_record['approval_statistics'] = approval_stats
            return user_record
            
        except Exception as e:
            raise Exception(f"Failed to get user statistics: {str(e)}")
    
    async def get_approval_analytics(self) -> Dict[str, Any]:
        """Get system-wide approval analytics"""
        try:
            # Scan all approval requests (in production, consider using aggregation)
            response = self.approval_table.scan()
            all_approvals = response.get('Items', [])
            
            current_time = datetime.utcnow()
            last_30_days = current_time - timedelta(days=30)
            
            total_requests = len(all_approvals)
            recent_requests = [a for a in all_approvals 
                             if datetime.fromisoformat(a['created_at']) > last_30_days]
            
            analytics = {
                'total_requests': total_requests,
                'last_30_days': {
                    'total_requests': len(recent_requests),
                    'approved': len([a for a in recent_requests if a['status'] == ApprovalStatus.APPROVED.value]),
                    'rejected': len([a for a in recent_requests if a['status'] == ApprovalStatus.REJECTED.value]),
                    'pending': len([a for a in recent_requests if a['status'] == ApprovalStatus.PENDING.value]),
                    'expired': len([a for a in recent_requests if a['status'] == ApprovalStatus.EXPIRED.value])
                },
                'overall_statistics': {
                    'approved': len([a for a in all_approvals if a['status'] == ApprovalStatus.APPROVED.value]),
                    'rejected': len([a for a in all_approvals if a['status'] == ApprovalStatus.REJECTED.value]),
                    'pending': len([a for a in all_approvals if a['status'] == ApprovalStatus.PENDING.value]),
                    'expired': len([a for a in all_approvals if a['status'] == ApprovalStatus.EXPIRED.value])
                },
                'average_approval_time': self._calculate_average_approval_time(all_approvals),
                'generated_at': current_time.isoformat()
            }
            
            return analytics
            
        except Exception as e:
            raise Exception(f"Failed to get approval analytics: {str(e)}")
    
    def _calculate_average_approval_time(self, approvals: List[Dict[str, Any]]) -> float:
        """Calculate average time from request to approval/rejection"""
        completed_approvals = [a for a in approvals 
                             if a['status'] in [ApprovalStatus.APPROVED.value, ApprovalStatus.REJECTED.value]
                             and a.get('approval_timestamp')]
        
        if not completed_approvals:
            return 0.0
        
        total_time = 0
        for approval in completed_approvals:
            created = datetime.fromisoformat(approval['created_at'])
            completed = datetime.fromisoformat(approval['approval_timestamp'])
            total_time += (completed - created).total_seconds()
        
        return total_time / len(completed_approvals) / 3600  # Return in hours