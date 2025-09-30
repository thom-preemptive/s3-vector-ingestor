# agent2_ingestor - Multi-Environment Deployment Guide

## 🎯 Quick Reference

### Environment URLs:
- **DEV**: https://dev.dn1hdu83qdv9u.amplifyapp.com
- **TEST**: https://test.dn1hdu83qdv9u.amplifyapp.com  
- **MAIN**: https://main.dn1hdu83qdv9u.amplifyapp.com

### Cognito Configuration:
| Environment | User Pool ID | Client ID |
|-------------|--------------|-----------|
| DEV | `us-east-1_ZXccV9Ntq` | `3u5hedl2mp0bvg5699l16dj4oe` |
| TEST | `us-east-1_epXBgyusk` | `7h6q69gsuoo77200knu88dmoe4` |
| MAIN | `us-east-1_KD9IBTRJl` | `4eq1gmn394e8ct1gpjra89vgak` |

## 🚀 Deployment Workflow

### 1. Development (DEV)
Work on the `dev` branch for active development:
```bash
git checkout dev
# Make your changes
git add .
git commit -m "Your changes"
git push origin dev
```
→ Auto-deploys to: https://dev.dn1hdu83qdv9u.amplifyapp.com

### 2. Testing (TEST)
Deploy stable features to TEST for QA:
```bash
git checkout test
git merge dev  # Merge latest dev changes
git push origin test
```
→ Auto-deploys to: https://test.dn1hdu83qdv9u.amplifyapp.com

### 3. Production (MAIN)
Deploy tested features to production:
```bash
git checkout main
git merge test  # Merge tested changes from test
git push origin main
```
→ Auto-deploys to: https://main.dn1hdu83qdv9u.amplifyapp.com
- EventBridge (create rules, targets)
- Cognito (create user pools)
- CloudFormation (deploy stacks)
- CloudWatch (logs, metrics)
- AWS Textract (document processing)
- AWS Bedrock (embeddings)

## Step-by-Step Deployment

### 1. Initial Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd agent2_ingestor

# Create and activate Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Verify AWS CLI configuration
aws sts get-caller-identity
```

### 2. Deploy Core AWS Infrastructure

```bash
cd infrastructure

# Deploy core services (S3, DynamoDB, Cognito)
python setup_aws.py

# Deploy queue infrastructure (SQS, DynamoDB tables)
python deploy_queue_infrastructure.py --environment dev --s3-bucket emergency-docs-bucket-us-east-1

# Deploy serverless orchestration (Lambda, EventBridge)  
python deploy_orchestration.py --environment dev

# Set up approval workflow
python setup_approval_workflow.py
```

### 3. Configure Environment Variables

After deployment, set these environment variables (replace with your actual values):

```bash
# Backend configuration
export AWS_REGION=us-east-1
export S3_BUCKET=emergency-docs-bucket-us-east-1
export DYNAMODB_TABLE=document-jobs
export COGNITO_USER_POOL_ID=<your-user-pool-id>
export COGNITO_CLIENT_ID=<your-client-id>
export DOC_PROCESSING_QUEUE=<your-queue-url>
export APPROVAL_QUEUE=<your-approval-queue-url>
export QUEUE_JOBS_TABLE=dev-emergency-docs-queue-jobs
export EVENTBRIDGE_BUS=dev-emergency-docs-event-bus

# Optional: Create .env file in backend directory
cat > backend/.env << EOF
AWS_REGION=us-east-1
S3_BUCKET=emergency-docs-bucket-us-east-1
DYNAMODB_TABLE=document-jobs
COGNITO_USER_POOL_ID=<your-user-pool-id>
COGNITO_CLIENT_ID=<your-client-id>
DOC_PROCESSING_QUEUE=<your-queue-url>
APPROVAL_QUEUE=<your-approval-queue-url>
QUEUE_JOBS_TABLE=dev-emergency-docs-queue-jobs
EVENTBRIDGE_BUS=dev-emergency-docs-event-bus
EOF
```

### 4. Test Backend Deployment

```bash
cd backend

# Test basic imports and AWS connectivity
python -c "
from services.aws_services import S3Service, DynamoDBService
from services.queue_service import JobQueueService
import asyncio

async def test_services():
    # Test S3
    s3 = S3Service()
    manifest = await s3.get_manifest()
    print(f'✅ S3 Service: Manifest version {manifest[\"version\"]}')
    
    # Test DynamoDB
    db = DynamoDBService()
    # This will work once we have a job to query
    
    # Test Queue Service
    queue = JobQueueService()
    stats = await queue.get_queue_statistics()
    print(f'✅ Queue Service: {len(stats)} queues configured')
    
    print('✅ All services configured correctly!')

asyncio.run(test_services())
"

# Start the backend server
python main.py
# Or use uvicorn directly:
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Test API Endpoints

Open a new terminal and test the API:

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test queue statistics
curl http://localhost:8000/queue/statistics

# Test dashboard overview
curl http://localhost:8000/dashboard/overview

# Test system health
curl http://localhost:8000/dashboard/health
```

### 6. Deploy Frontend (Optional for Testing)

```bash
cd frontend

# Install dependencies
npm install

# Configure environment variables
cat > .env.local << EOF
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_AWS_REGION=us-east-1
REACT_APP_COGNITO_USER_POOL_ID=<your-user-pool-id>
REACT_APP_COGNITO_CLIENT_ID=<your-client-id>
EOF

# Start development server
npm start
# Frontend will be available at http://localhost:3000
```

## Comprehensive Testing

### 1. Unit Tests for Services

```bash
cd backend

# Test AWS services integration
python -c "
import asyncio
from services.aws_services import S3Service

async def test_s3_operations():
    s3 = S3Service()
    
    # Test manifest operations
    manifest = await s3.get_manifest()
    print(f'✅ Manifest: {manifest[\"document_count\"]} documents')
    
    # Test statistics
    stats = await s3.get_manifest_statistics()
    print(f'✅ Statistics: {stats}')
    
    # Test backup
    backup_path = await s3.backup_manifest()
    print(f'✅ Backup created: {backup_path}')

asyncio.run(test_s3_operations())
"

# Test queue operations
python -c "
import asyncio
from services.queue_service import JobQueueService
from services.queue_service import QueueType, JobPriority

async def test_queue_operations():
    queue = JobQueueService()
    
    # Test job enqueueing
    job_data = {
        'job_id': 'test-job-123',
        'job_name': 'Test Job',
        'source_type': 'url',
        'source_data': 'https://example.com',
        'user_id': 'test-user',
        'metadata': {'test': True}
    }
    
    job_id = await queue.enqueue_job(
        QueueType.DOCUMENT_PROCESSING,
        job_data,
        JobPriority.NORMAL
    )
    print(f'✅ Job enqueued: {job_id}')
    
    # Test statistics
    stats = await queue.get_queue_statistics()
    print(f'✅ Queue stats: {stats}')

asyncio.run(test_queue_operations())
"
```

### 2. End-to-End Document Processing Test

```bash
# Test URL processing via API
curl -X POST http://localhost:8000/queue/process/urls \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "job_name": "Test URL Processing",
    "user_id": "test-user",
    "priority": 2,
    "requires_approval": false
  }'

# Check job status (replace with actual job_id from response)
curl http://localhost:8000/queue/jobs/test-job-123/status

# Monitor processing in real-time
curl http://localhost:8000/dashboard/overview
```

### 3. Test PDF Processing (with sample file)

```bash
# Create a simple test PDF (if you have one)
curl -X POST http://localhost:8000/queue/process/pdf \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/test.pdf" \
  -F "job_name=Test PDF Processing" \
  -F "user_id=test-user" \
  -F "priority=2" \
  -F "requires_approval=false"
```

### 4. Test Monitoring Dashboard

```bash
# Open the monitoring dashboard
open http://localhost:3000/dashboard

# Or test dashboard API endpoints
curl http://localhost:8000/dashboard/health
curl http://localhost:8000/dashboard/queues  
curl http://localhost:8000/dashboard/workers
curl http://localhost:8000/dashboard/metrics/performance
```

## Production Deployment

### 1. Environment-Specific Configuration

```bash
# Deploy production infrastructure
cd infrastructure

# Production deployment with enhanced settings
python setup_aws.py --environment prod --enable-backup --enable-monitoring
python deploy_queue_infrastructure.py --environment prod --s3-bucket emergency-docs-prod-bucket
python deploy_orchestration.py --environment prod --enable-xray
```

### 2. Frontend Production Deployment

```bash
# Using AWS Amplify
cd frontend
npm install -g @aws-amplify/cli
amplify configure
amplify init
amplify publish

# Or using manual S3 + CloudFront deployment
npm run build
aws s3 sync build/ s3://your-frontend-bucket/
```

### 3. CI/CD Pipeline Setup

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Emergency Document Processor

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
        
    - name: Deploy infrastructure
      run: |
        cd infrastructure
        python setup_aws.py --environment prod
        python deploy_queue_infrastructure.py --environment prod
        python deploy_orchestration.py --environment prod
```

## Monitoring & Operations

### 1. CloudWatch Dashboard

Access your monitoring dashboard at:
- AWS Console → CloudWatch → Dashboards → `dev-emergency-docs-queue-monitoring`

### 2. Log Monitoring

```bash
# View Lambda function logs
aws logs tail /aws/lambda/dev-document-orchestrator --follow
aws logs tail /aws/lambda/dev-document-processor --follow

# View API Gateway logs
aws logs tail API-Gateway-Execution-Logs_${API_ID}/dev --follow
```

### 3. Performance Monitoring

```bash
# Check queue metrics
aws sqs get-queue-attributes --queue-url $DOC_PROCESSING_QUEUE --attribute-names All

# Check DynamoDB metrics
aws dynamodb describe-table --table-name $QUEUE_JOBS_TABLE
```

## Troubleshooting

### Common Issues

1. **Lambda timeout errors**
   ```bash
   # Increase timeout in serverless-orchestration.yaml
   Timeout: 300  # 5 minutes
   ```

2. **Permission errors**
   ```bash
   # Check IAM roles in AWS Console
   # Ensure Lambda execution role has necessary permissions
   ```

3. **Queue processing stuck**
   ```bash
   # Check dead letter queues
   aws sqs receive-message --queue-url $DOC_PROCESSING_QUEUE_DLQ
   ```

4. **S3 upload failures**
   ```bash
   # Verify bucket policy and CORS configuration
   aws s3api get-bucket-policy --bucket $S3_BUCKET
   ```

### Health Checks

```bash
# Complete system health check
python -c "
import asyncio
from services.aws_services import S3Service
from services.queue_service import JobQueueService

async def health_check():
    print('🔍 Running health checks...')
    
    # S3 Health
    s3 = S3Service()
    try:
        manifest = await s3.get_manifest()
        print(f'✅ S3: Manifest accessible, {manifest[\"document_count\"]} docs')
    except Exception as e:
        print(f'❌ S3: {e}')
    
    # Queue Health
    queue = JobQueueService()
    try:
        stats = await queue.get_queue_statistics()
        print(f'✅ Queues: {len(stats)} queues operational')
    except Exception as e:
        print(f'❌ Queues: {e}')
    
    print('🎯 Health check complete!')

asyncio.run(health_check())
"
```

## Security Checklist

- [ ] AWS credentials properly configured
- [ ] S3 bucket access restricted to application
- [ ] DynamoDB tables encrypted at rest
- [ ] Lambda functions have minimal IAM permissions
- [ ] API Gateway has rate limiting enabled
- [ ] Cognito user pool configured with strong password policy
- [ ] CloudWatch logs retention set appropriately
- [ ] VPC configuration for Lambda (if required)

## Performance Optimization

- [ ] Lambda function memory allocation optimized
- [ ] DynamoDB read/write capacity configured
- [ ] S3 transfer acceleration enabled (if needed)
- [ ] CloudWatch log retention policies set
- [ ] Dead letter queue retention periods configured

Your emergency document processor is now ready for deployment and testing! 🚀

The system is designed to be resilient, scalable, and cost-effective with comprehensive monitoring and error handling built-in.