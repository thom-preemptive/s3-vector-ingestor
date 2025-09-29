# Emergency Document Processor

# agent2_ingestor

A cloud-ready serverless document processing system that converts PDFs and web content into markdown with vector embeddings for AI/ML applications.

## Architecture Overview

This system uses a serverless, event-driven architecture with:

- **Backend**: Python FastAPI with comprehensive API endpoints
- **Frontend**: React TypeScript with Material-UI and AWS Amplify
- **Queue System**: SQS-based job queuing with DynamoDB job tracking
- **Storage**: S3 for documents and vector sidecars
- **Authentication**: AWS Cognito for multi-user support
- **Processing**: AWS Textract (OCR) + Bedrock Titan (embeddings)
- **Monitoring**: Real-time dashboard with CloudWatch metrics

## Project Structure

```
├── backend/                    # FastAPI backend
│   ├── main.py                # Main API server
│   ├── dashboard_api.py       # Dashboard monitoring endpoints
│   └── services/              # Business logic services
│       ├── aws_services.py    # AWS service integrations
│       ├── queue_service.py   # Job queue management
│       ├── document_processor.py  # Document processing
│       ├── approval_service.py    # Approval workflows
│       └── orchestration_service.py  # Event orchestration
├── frontend/                  # React frontend
│   └── src/
│       └── components/        # React components
├── infrastructure/           # CloudFormation templates
│   ├── serverless-orchestration.yaml  # Lambda & EventBridge
│   ├── queue-infrastructure.yaml      # SQS & DynamoDB
│   └── deployment scripts
└── lambda/                   # Lambda functions
    ├── document_orchestrator.py  # Event orchestration
    └── document_processor.py     # Document processing worker
```

## Features

✅ **Multi-User Authentication**
- AWS Cognito integration with user pools
- Role-based access control (admin/user)
- JWT token authentication

✅ **Document Processing Pipeline**
- PDF upload with OCR support (AWS Textract)
- URL scraping and processing
- Markdown conversion with vector embeddings
- Sidecar file generation for AI integration

✅ **Job Queue System**
- SQS-based reliable message queuing
- Priority-based job processing
- Retry logic with dead letter queues
- Real-time job status tracking

✅ **Approval Workflows**
- Configurable approval requirements
- Multi-stage approval process
- Activity tracking and audit logs
- Notification system

✅ **Real-Time Monitoring**
- System health dashboard
- Queue metrics and visualization
- Active worker monitoring
- Performance analytics

✅ **Serverless Orchestration**
- Event-driven architecture with EventBridge
- Lambda-based processing workers
- Auto-scaling based on queue depth
- Cost-optimized serverless design

## 🚀 Quick Deploy to AWS Amplify

For rapid deployment to AWS Amplify:

```bash
# Run the automated deployment script
./deploy-amplify.sh

# Or follow the detailed step-by-step guide
cat AMPLIFY_DEPLOYMENT.md
```

This will set up:
- ✅ Frontend hosting on Amplify
- ✅ Automated builds and deployments
- ✅ SSL certificate and custom domain support
- ✅ Environment variable configuration
- ✅ CI/CD pipeline with Git integration

## Prerequisites

- AWS Account with appropriate permissions
- Python 3.9+ with pip
- Node.js 16+ with npm
- AWS CLI configured
- Docker (optional, for local development)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd agent2_ingestor
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Deploy AWS Infrastructure

```bash
# Deploy core AWS services (S3, DynamoDB, Cognito)
cd infrastructure
python setup_aws.py --environment dev --region us-east-1

# Deploy queue infrastructure
python deploy_queue_infrastructure.py --environment dev --s3-bucket your-bucket-name

# Deploy serverless orchestration
python deploy_orchestration.py --environment dev
```

### 4. Configure Environment Variables

Copy the environment variables output from the infrastructure deployment and set them:

```bash
# Backend environment variables
export AWS_REGION=us-east-1
export S3_BUCKET=your-bucket-name
export DYNAMODB_TABLE=your-table-name
export COGNITO_USER_POOL_ID=your-user-pool-id
export COGNITO_CLIENT_ID=your-client-id
export DOC_PROCESSING_QUEUE=your-queue-url
export QUEUE_JOBS_TABLE=your-jobs-table
```

### 5. Start the Backend

```bash
cd backend
python main.py
# Server will start on http://localhost:8000
```

### 6. Start the Frontend

```bash
cd frontend
npm install
npm start
# Frontend will start on http://localhost:3000
```

## API Documentation

### Authentication Endpoints

- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh tokens
- `POST /auth/create-user` - Create new user (admin)

### Document Processing

- `POST /upload/pdf` - Upload PDF files
- `POST /process/urls` - Process URLs
- `POST /queue/process/pdf` - Queue PDF processing (recommended)
- `POST /queue/process/urls` - Queue URL processing (recommended)

### Job Management

- `GET /jobs` - List user jobs
- `GET /jobs/{job_id}` - Get job details
- `GET /queue/jobs/{job_id}/status` - Get queue job status
- `POST /jobs/{job_id}/cancel` - Cancel job

### Approval Workflows

- `POST /approvals/request` - Request approval
- `POST /approvals/approve` - Approve request
- `POST /approvals/reject` - Reject request

### Monitoring Dashboard

- `GET /dashboard/health` - System health status
- `GET /dashboard/overview` - Dashboard overview
- `GET /dashboard/queues` - Queue statistics
- `GET /dashboard/workers` - Worker status
- `GET /dashboard/metrics/performance` - Performance metrics

## System Health Monitoring

The system includes comprehensive monitoring:

### CloudWatch Dashboard
Access at: AWS Console → CloudWatch → Dashboards → `{environment}-emergency-docs-queue-monitoring`

### Real-Time Dashboard
Access at: `http://localhost:3000/dashboard` (after starting frontend)

### Key Metrics
- **Queue Health**: Messages pending, processing, failed
- **Processing Performance**: Throughput, latency, error rates
- **Worker Status**: Active workers, job distribution
- **System Health**: Overall health score and alerts

## Configuration

### Queue Configuration

```python
# Queue types and their purposes
QueueType.DOCUMENT_PROCESSING  # PDF/URL processing jobs
QueueType.APPROVAL_WORKFLOW    # Approval request processing
QueueType.MAINTENANCE          # System maintenance tasks
```

### Job Priorities

```python
JobPriority.URGENT = 4    # Process immediately
JobPriority.HIGH = 3      # High priority
JobPriority.NORMAL = 2    # Default priority
JobPriority.LOW = 1       # Background processing
```

### Processing Pipeline

1. **Document Ingestion**: PDFs uploaded or URLs submitted
2. **Queue Processing**: Jobs queued with priority and retry logic
3. **Content Extraction**: OCR for PDFs, scraping for URLs
4. **Markdown Conversion**: Clean, structured markdown output
5. **Vector Generation**: Bedrock Titan embeddings
6. **Storage**: S3 upload of markdown + vector sidecar
7. **Approval**: Optional approval workflow
8. **Completion**: Job marked complete, notifications sent

## Deployment

### Development Environment

```bash
# Deploy with dev configuration
./infrastructure/setup_aws.py --environment dev
```

### Production Environment

```bash
# Deploy with production configuration
./infrastructure/setup_aws.py --environment prod --enable-backup --enable-monitoring
```

### CI/CD Integration

The system supports automated deployment through:
- AWS CodePipeline
- GitHub Actions
- Custom deployment scripts

## Troubleshooting

### Common Issues

1. **Queue not processing jobs**
   - Check Lambda function logs in CloudWatch
   - Verify SQS queue permissions
   - Check DLQ for failed messages

2. **Authentication failures**
   - Verify Cognito configuration
   - Check JWT token expiration
   - Validate user pool settings

3. **Document processing errors**
   - Check S3 bucket permissions
   - Verify Textract service limits
   - Review Bedrock access permissions

### Monitoring Commands

```bash
# Check queue statistics
python -c "from services.queue_service import JobQueueService; import asyncio; print(asyncio.run(JobQueueService().get_queue_statistics()))"

# Test infrastructure
python infrastructure/deploy_queue_infrastructure.py --test

# View CloudWatch logs
aws logs tail /aws/lambda/document-processor --follow
```

## Security

- All API endpoints require authentication
- S3 buckets use server-side encryption
- DynamoDB tables have encryption at rest
- VPC isolation for Lambda functions
- IAM roles follow least privilege principle

## Performance

- **Throughput**: 100+ documents/hour (depending on size)
- **Scalability**: Auto-scaling Lambda workers
- **Latency**: <30s for typical document processing
- **Availability**: 99.9% uptime with multi-AZ deployment

## Cost Optimization

- Serverless architecture minimizes costs
- S3 Intelligent Tiering for storage optimization
- Lambda execution time optimized
- DynamoDB on-demand billing
- CloudWatch log retention policies

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review CloudWatch logs and metrics
3. Consult AWS service documentation
4. Create an issue in the project repository

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Emergency Document Processor** - Built for resilient, scalable emergency document management.
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials and settings
   ```

3. **Set up AWS infrastructure:**
   ```bash
   cd ../infrastructure
   python setup_aws.py
   ```

4. **Start the backend server:**
   ```bash
   cd ../backend
   uvicorn main:app --reload
   ```

### Frontend Setup

1. **Install Node.js dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure Amplify (optional for local dev):**
   ```bash
   npm install -g @aws-amplify/cli
   amplify configure
   amplify init
   ```

3. **Start the development server:**
   ```bash
   npm start
   ```

## API Endpoints

### Authentication
- All endpoints require Bearer token authentication
- Use AWS Cognito for user management

### Document Processing
- `POST /upload/pdf` - Upload PDF files for processing
- `POST /process/urls` - Submit URLs for processing
- `GET /jobs/{job_id}` - Get job status
- `GET /jobs` - List user jobs
- `POST /approve` - Approve/reject jobs

## Usage

1. **Upload Documents**: Use the web interface to upload PDF files or enter URLs
2. **Job Creation**: Specify job name and approval requirements  
3. **Processing**: Documents are processed into markdown + vector sidecars
4. **Approval**: If required, jobs await approval before S3 upload
5. **Storage**: Approved documents are uploaded to S3 with manifest updates

## Output Format

### Markdown Files
- Clean markdown format with metadata headers
- Preserved document structure
- Processing timestamps and source information

### Vector Sidecars
- JSON format with embeddings from Bedrock Titan
- 1024-token chunks for optimal vector search
- Metadata for each chunk including source and position

### Manifest Updates
- Central JSON manifest file in S3
- Tracks all processed documents
- Enables efficient document discovery and indexing

## Configuration

### Environment Variables
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET=emergency-docs-bucket
DYNAMODB_TABLE=document-jobs
MANIFEST_KEY=manifest.json
COGNITO_USER_POOL_ID=your_user_pool_id
COGNITO_CLIENT_ID=your_client_id
```

### S3 Bucket Structure
```
emergency-docs-bucket/
├── manifest.json
├── documents/
│   ├── {job_id}/
│   │   ├── {filename}.md
│   │   └── {filename}.sidecar.json
└── uploads/
    └── {job_id}/
        └── original_files/
```

## Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests  
cd frontend
npm test
```

### Deployment
- Backend: Deploy to AWS Lambda or EC2
- Frontend: Deploy with AWS Amplify
- Infrastructure: Use AWS CloudFormation or CDK

## Security Considerations

- All API endpoints require authentication
- S3 bucket policies configured for appropriate access
- Cognito handles user authentication and authorization
- Environment variables for sensitive configuration

## Monitoring

- CloudWatch logs for backend monitoring
- DynamoDB for job status tracking
- S3 event notifications for processing pipeline
- Amplify hosting metrics for frontend

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test thoroughly
4. Submit a pull request with detailed description

## License

This project is licensed under the MIT License - see the LICENSE file for details.