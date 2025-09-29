#!/usr/bin/env python3
"""
Simple queue infrastructure deployment without complex monitoring.
For initial testing and development.
"""

import boto3
import json
import time

def create_sqs_queues():
    """Create basic SQS queues for job processing."""
    sqs = boto3.client('sqs', region_name='us-east-1')
    
    queues = {
        'document_processing': 'dev-emergency-docs-processing',
        'approval_workflow': 'dev-emergency-docs-approval',
        'maintenance': 'dev-emergency-docs-maintenance'
    }
    
    queue_urls = {}
    
    for queue_type, queue_name in queues.items():
        try:
            # Create main queue
            response = sqs.create_queue(
                QueueName=queue_name,
                Attributes={
                    'VisibilityTimeoutSeconds': '900',  # 15 minutes
                    'MessageRetentionPeriod': '1209600',  # 14 days
                    'ReceiveMessageWaitTimeSeconds': '20',  # Long polling
                }
            )
            queue_urls[queue_type] = response['QueueUrl']
            print(f"✅ Created queue: {queue_name}")
            
            # Create DLQ
            dlq_response = sqs.create_queue(
                QueueName=f"{queue_name}-dlq",
                Attributes={
                    'MessageRetentionPeriod': '1209600',  # 14 days
                }
            )
            queue_urls[f"{queue_type}_dlq"] = dlq_response['QueueUrl']
            print(f"✅ Created DLQ: {queue_name}-dlq")
            
        except sqs.exceptions.QueueNameExists:
            # Get existing queue URL
            response = sqs.get_queue_url(QueueName=queue_name)
            queue_urls[queue_type] = response['QueueUrl']
            print(f"✅ Queue already exists: {queue_name}")
            
            try:
                dlq_response = sqs.get_queue_url(QueueName=f"{queue_name}-dlq")
                queue_urls[f"{queue_type}_dlq"] = dlq_response['QueueUrl']
                print(f"✅ DLQ already exists: {queue_name}-dlq")
            except:
                pass
                
        except Exception as e:
            print(f"❌ Error creating queue {queue_name}: {e}")
    
    return queue_urls

def create_dynamodb_table():
    """Create DynamoDB table for job tracking."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    table_name = 'dev-emergency-docs-queue-jobs'
    
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'job_id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'job_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'status',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'user_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                },
                {
                    'IndexName': 'StatusIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'status',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {
                    'Key': 'Environment',
                    'Value': 'dev'
                },
                {
                    'Key': 'Service',
                    'Value': 'EmergencyDocProcessor'
                }
            ]
        )
        
        # Wait for table to be created
        print("⏳ Waiting for DynamoDB table to be created...")
        table.wait_until_exists()
        print(f"✅ Created DynamoDB table: {table_name}")
        
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print(f"✅ DynamoDB table already exists: {table_name}")
    except Exception as e:
        print(f"❌ Error creating DynamoDB table: {e}")

def main():
    """Deploy simple queue infrastructure."""
    print("🚀 Deploying Simple Queue Infrastructure")
    print("=" * 50)
    
    # Create SQS queues
    print("\n📋 Creating SQS Queues...")
    queue_urls = create_sqs_queues()
    
    # Create DynamoDB table
    print("\n💾 Creating DynamoDB Table...")
    create_dynamodb_table()
    
    # Output configuration
    print("\n" + "=" * 50)
    print("📋 INFRASTRUCTURE DEPLOYED")
    print("=" * 50)
    print("\n🔧 Environment Variables:")
    print("export AWS_REGION=us-east-1")
    print("export S3_BUCKET=emergency-docs-bucket-us-east-1")
    print("export DYNAMODB_TABLE=document-jobs")
    print("export QUEUE_JOBS_TABLE=dev-emergency-docs-queue-jobs")
    print("export COGNITO_USER_POOL_ID=us-east-1_jc5vhIeqd")
    print("export COGNITO_CLIENT_ID=2p1hqn2mgqlroaerlm02b0qgvu")
    
    if 'document_processing' in queue_urls:
        print(f"export DOC_PROCESSING_QUEUE={queue_urls['document_processing']}")
    if 'approval_workflow' in queue_urls:
        print(f"export APPROVAL_QUEUE={queue_urls['approval_workflow']}")
    if 'maintenance' in queue_urls:
        print(f"export MAINTENANCE_QUEUE={queue_urls['maintenance']}")
    
    print("\n📖 Next Steps:")
    print("1. Copy the environment variables above")
    print("2. Set them in your shell: export VAR=value")
    print("3. Start the backend: cd ../backend && python main.py")
    print("4. Test the API: curl http://localhost:8000/health")

if __name__ == "__main__":
    main()