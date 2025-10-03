# EventBridge Async Processing Architecture

## Overview
The system now uses **AWS EventBridge** for true asynchronous document processing, eliminating API Gateway timeout issues.

## Architecture Flow

```
User uploads file → Frontend → API Gateway → Lambda (FastAPI)
                                                  ↓
                                         Create job in DynamoDB
                                         (status: "queued")
                                                  ↓
                                         Send event to EventBridge
                                                  ↓
                                         Return job_id immediately
                                                  ↓
EventBridge → Lambda (same function, different handler) → Process documents
                                                             ↓
                                                   Update DynamoDB
                                                   (status: "completed")
```

## Components

### 1. EventBridge Event Bus
- **Name**: `agent2-ingestor-events-dev`
- **Purpose**: Decoupled message bus for async processing
- **Stack**: `agent2-ingestor-eventbridge-dev`

### 2. EventBridge Rule
- **Name**: `agent2-ingestor-document-processing-dev`
- **Event Pattern**: Listens for `source: agent2.ingestor` with detail-type `Document Processing Required`
- **Target**: Lambda function `agent2-ingestor-api-dev`
- **Retry**: Up to 2 retries on failure

### 3. Lambda Handler
The Lambda function now handles **two types of events**:

#### HTTP Requests (via API Gateway)
```python
# Routed to FastAPI via Mangum
event = {
    "httpMethod": "POST",
    "path": "/upload/process-s3-files",
    ...
}
```

#### EventBridge Events (async processing)
```python
# Routed to process_job_async()
event = {
    "source": "agent2.ingestor",
    "detail-type": "Document Processing Required",
    "detail": {
        "job_id": "...",
        "user_id": "...",
        "files": [...],
        ...
    }
}
```

### 4. API Endpoint: `/upload/process-s3-files`

**New Behavior:**
1. Creates job in DynamoDB with status `queued`
2. Sends event to EventBridge
3. **Returns immediately** with job_id (no timeout!)
4. Processing happens asynchronously in background

**Response:**
```json
{
  "job_id": "89fdf15c-...",
  "status": "queued",
  "files_count": 1,
  "message": "Job created and queued for processing. Check Jobs page for status."
}
```

## Status Lifecycle

1. **queued** - Job created, event sent to EventBridge
2. **processing** - Lambda picked up event and started processing (updated by process_job_async)
3. **completed** - Processing finished successfully
4. **failed** - Processing encountered an error

## Benefits

✅ **No API Gateway timeouts** - API returns immediately  
✅ **Scalable** - EventBridge handles high throughput  
✅ **Reliable** - Automatic retries (2x) on failure  
✅ **Decoupled** - Easy to add more processing stages  
✅ **Observable** - CloudWatch logs for both HTTP and EventBridge invocations  

## Deployment

### Deploy EventBridge Infrastructure
```bash
cd infrastructure
./deploy-eventbridge.sh
```

### Deploy Backend
```bash
cd backend
sam build && sam deploy
```

## Monitoring

### Check EventBridge Events
```bash
aws events list-rules --event-bus-name agent2-ingestor-events-dev --region us-east-1
```

### View Lambda Logs
```bash
aws logs tail /aws/lambda/agent2-ingestor-api-dev --follow
```

### Check Job Status
Jobs page auto-refreshes every 10 seconds to show real-time status updates.

## Environment Variables

### Backend Lambda
- `EVENT_BUS_NAME`: `agent2-ingestor-events-dev`
- `S3_BUCKET`: `agent2-ingestor-bucket-us-east-1`
- `COGNITO_USER_POOL_ID`: `us-east-1_Yk8Yt64uE`

## Troubleshooting

### Event not triggering Lambda
1. Check EventBridge rule is ENABLED: `aws events describe-rule --name agent2-ingestor-document-processing-dev --event-bus-name agent2-ingestor-events-dev`
2. Check Lambda has permission: Look for `EventBridgeInvokeLambdaPermission` in CloudFormation
3. Check CloudWatch logs: `/aws/lambda/agent2-ingestor-api-dev`

### Job stuck in "queued" status
- Event may have failed - check CloudWatch logs
- EventBridge may be throttling - check metrics
- Lambda may have errored - check Lambda errors in CloudWatch

## Files Changed

- `infrastructure/eventbridge-setup.yaml` - EventBridge CloudFormation template
- `infrastructure/deploy-eventbridge.sh` - Deployment script
- `backend/template.yaml` - Added EVENT_BUS_NAME env var, Lambda ARN output
- `backend/lambda_handler.py` - Routes EventBridge events to process_job_async()
- `backend/main.py` - Updated /upload/process-s3-files to use EventBridge
- `backend/services/orchestration_service.py` - Updated source to 'agent2.ingestor'
