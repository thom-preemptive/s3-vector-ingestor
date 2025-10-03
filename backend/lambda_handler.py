"""
AWS Lambda handler for agent2_ingestor FastAPI application.
This file adapts the FastAPI app to work with AWS Lambda and API Gateway.
Also handles async processing events from Lambda self-invocation.
"""

import asyncio
import boto3
import os
from mangum import Mangum
from main import app

# Initialize AWS clients and services
s3_client = boto3.client('s3', region_name='us-east-1')
S3_BUCKET = os.getenv("S3_BUCKET", "agent2-ingestor-bucket-us-east-1")

# Create the Lambda handler
mangum_handler = Mangum(app, lifespan="off")

def handler(event, context):
    """
    Main Lambda handler.
    
    Routes:
    - HTTP requests -> FastAPI via Mangum
    - EventBridge events -> process_job_async()
    """
    
    # Check if this is an EventBridge event
    if isinstance(event, dict) and event.get('source') == 'agent2.ingestor':
        # This is an EventBridge event for document processing
        detail = event.get('detail', {})
        return asyncio.run(process_job_async(detail))
    else:
        # This is an HTTP request from API Gateway - route to FastAPI
        return mangum_handler(event, context)

async def process_job_async(event):
    """
    Process documents asynchronously.
    Called via Lambda self-invocation to avoid API Gateway timeout.
    """
    from services.aws_services import DynamoDBService
    from services.document_processor import DocumentProcessor
    
    dynamodb_service = DynamoDBService()
    document_processor = DocumentProcessor()
    
    job_id = event['job_id']
    user_id = event['user_id']
    job_name = event['job_name']
    files = event['files']
    
    try:
        # Download files from S3
        file_contents = []
        filenames = []
        
        for file_info in files:
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=file_info['file_key'])
            file_contents.append(response['Body'].read())
            filenames.append(file_info['filename'])
        
        # Process documents
        processing_result = await document_processor.process_job(
            job_id=job_id,
            files=file_contents,
            filenames=filenames,
            user_id=user_id,
            job_name=job_name
        )
        
        # Update job status to completed
        await dynamodb_service.update_job_status(
            job_id, 
            'completed',
            documents_processed=processing_result['successful_documents'],
            processing_summary=f"Successfully processed {processing_result['successful_documents']} of {processing_result['total_documents']} documents"
        )
        
        return {
            'statusCode': 200,
            'body': {'message': 'Job processed successfully', 'job_id': job_id}
        }
        
    except Exception as e:
        # Mark job as failed
        await dynamodb_service.mark_job_failed(job_id, str(e))
        return {
            'statusCode': 500,
            'body': {'message': 'Job processing failed', 'error': str(e), 'job_id': job_id}
        }