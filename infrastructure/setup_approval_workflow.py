#!/usr/bin/env python3
"""
Setup script for approval workflow and user tracking infrastructure
Creates necessary DynamoDB tables for the emergency document processor
"""

import boto3
import json
import time
from datetime import datetime

def create_approval_tables():
    """Create approval workflow and user tracking DynamoDB tables"""
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    tables_to_create = []
    
    # Approval table configuration
    approval_table_config = {
        'TableName': 'document-approvals',
        'KeySchema': [
            {'AttributeName': 'approval_id', 'KeyType': 'HASH'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'approval_id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'status', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'}
        ],
        'GlobalSecondaryIndexes': [
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
        'BillingMode': 'PAY_PER_REQUEST'
    }
    
    # User tracking table configuration
    user_tracking_table_config = {
        'TableName': 'user-tracking',
        'KeySchema': [
            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'last_activity', 'AttributeType': 'S'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'LastActivityIndex',
                'KeySchema': [
                    {'AttributeName': 'last_activity', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        'BillingMode': 'PAY_PER_REQUEST'
    }
    
    # Check if tables exist and create if needed
    for table_config in [approval_table_config, user_tracking_table_config]:
        table_name = table_config['TableName']
        
        try:
            # Try to get table
            table = dynamodb.Table(table_name)
            table.load()
            print(f"✓ Table '{table_name}' already exists")
            
        except dynamodb.meta.client.exceptions.ResourceNotFoundException:
            print(f"Creating table '{table_name}'...")
            
            try:
                table = dynamodb.create_table(**table_config)
                tables_to_create.append((table_name, table))
                print(f"✓ Table '{table_name}' creation initiated")
                
            except Exception as e:
                print(f"❌ Failed to create table '{table_name}': {str(e)}")
                return False
    
    # Wait for all tables to be created
    if tables_to_create:
        print("\nWaiting for tables to be created...")
        
        for table_name, table in tables_to_create:
            print(f"Waiting for '{table_name}' to be active...")
            try:
                table.wait_until_exists()
                print(f"✓ Table '{table_name}' is now active")
            except Exception as e:
                print(f"❌ Error waiting for table '{table_name}': {str(e)}")
                return False
    
    print("\n🎉 All approval workflow tables are ready!")
    return True

def verify_tables():
    """Verify that all tables were created successfully"""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    required_tables = ['document-approvals', 'user-tracking']
    
    print("\nVerifying table creation...")
    
    for table_name in required_tables:
        try:
            table = dynamodb.Table(table_name)
            table.load()
            
            # Get table description
            response = table.meta.client.describe_table(TableName=table_name)
            table_info = response['Table']
            
            print(f"\n✓ Table: {table_name}")
            print(f"  Status: {table_info['TableStatus']}")
            print(f"  Billing Mode: {table_info.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')}")
            print(f"  Item Count: {table_info['ItemCount']}")
            
            # List GSIs
            gsis = table_info.get('GlobalSecondaryIndexes', [])
            if gsis:
                print(f"  Global Secondary Indexes:")
                for gsi in gsis:
                    print(f"    - {gsi['IndexName']}: {gsi['IndexStatus']}")
            
        except Exception as e:
            print(f"❌ Failed to verify table '{table_name}': {str(e)}")
            return False
    
    return True

def create_sample_data():
    """Create some sample approval workflow data for testing"""
    print("\nCreating sample approval workflow data...")
    
    try:
        # Import the approval service
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
        
        from services.approval_service import ApprovalService
        import asyncio
        
        async def create_samples():
            approval_service = ApprovalService()
            
            # Sample user IDs (would be real Cognito user IDs in production)
            sample_users = [
                'user-123e4567-e89b-12d3-a456-426614174000',
                'user-987f6543-e21c-34d5-b678-543216789abc'
            ]
            
            sample_documents = [
                {
                    'filename': 'emergency_plan.pdf',
                    'type': 'pdf',
                    'size': 1024000,
                    'processed_at': datetime.utcnow().isoformat()
                },
                {
                    'filename': 'evacuation_procedures.pdf', 
                    'type': 'pdf',
                    'size': 2048000,
                    'processed_at': datetime.utcnow().isoformat()
                }
            ]
            
            # Create a sample approval request
            approval_id = await approval_service.create_approval_request(
                job_id='job-sample-12345',
                user_id=sample_users[0],
                document_list=sample_documents,
                request_reason='Testing approval workflow for emergency documents'
            )
            
            print(f"✓ Created sample approval request: {approval_id}")
            
            # Track some sample user activities
            for i, user_id in enumerate(sample_users):
                await approval_service.track_user_activity(
                    user_id=user_id,
                    activity_type='system_test',
                    metadata={
                        'test_setup': True,
                        'user_number': i + 1,
                        'created_at': datetime.utcnow().isoformat()
                    }
                )
                print(f"✓ Created sample user activity for user {i + 1}")
            
            return True
        
        # Run the async function
        result = asyncio.run(create_samples())
        
        if result:
            print("✓ Sample data created successfully!")
        else:
            print("❌ Failed to create sample data")
            
    except Exception as e:
        print(f"❌ Error creating sample data: {str(e)}")
        print("This is expected if running outside AWS environment")

def main():
    """Main setup function"""
    print("Emergency Document Processor - Approval Workflow Setup")
    print("=" * 60)
    print(f"Setup started at: {datetime.utcnow().isoformat()}")
    print()
    
    try:
        # Create tables
        if not create_approval_tables():
            print("❌ Failed to create tables")
            return False
        
        # Verify tables
        if not verify_tables():
            print("❌ Failed to verify tables")
            return False
        
        # Create sample data (optional)
        create_sample_data()
        
        print("\n" + "=" * 60)
        print("🎉 Approval workflow setup completed successfully!")
        print("\nNext steps:")
        print("1. Update environment variables:")
        print("   - APPROVAL_TABLE=document-approvals")
        print("   - USER_TRACKING_TABLE=user-tracking")
        print("2. Deploy the updated application")
        print("3. Test the approval workflow endpoints")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)