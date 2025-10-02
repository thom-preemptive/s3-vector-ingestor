# Backend API Deployment Guide

## Current Status
The backend FastAPI application is ready for deployment with the following infrastructure prepared:
- **SAM Template**: `template.yaml` for Lambda + API Gateway
- **Lambda Handler**: `lambda_handler.py` with Mangum adapter
- **Deployment Script**: `deploy.sh` for automated deployment

## Deployment Options

### Option 1: AWS Lambda + API Gateway (SAM) - PREFERRED
**Status**: Infrastructure ready, requires API Gateway IAM permissions

**Prerequisites**:
- AWS CLI configured
- SAM CLI installed
- API Gateway IAM permissions (currently missing)

**Deploy command**:
```bash
cd backend
./deploy.sh
```

**Required IAM permissions** (needs to be added to user/role):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "apigateway:*",
                "lambda:*",
                "iam:*",
                "cloudformation:*"
            ],
            "Resource": "*"
        }
    ]
}
```

### Option 2: Container Deployment (Alternative)
For immediate deployment without API Gateway permissions:

1. **AWS App Runner**: Deploy FastAPI as a container
2. **AWS ECS Fargate**: Container service deployment
3. **Local Docker**: For development testing

## Current Frontend Configuration

The frontend is configured to work with demo data when no backend API is available:
- **Dev environment**: `.env.dev` has no API URL (commented out)
- **Error handling**: Graceful fallback to demo data
- **Jobs page**: Shows realistic demo jobs with status indicators

## Next Steps

1. **Configure IAM permissions** for API Gateway deployment
2. **Deploy backend** using `./deploy.sh`
3. **Update frontend** environment variables with deployed API URL
4. **Test integration** between frontend and backend

## Endpoints Available
Once deployed, the API will provide:
- `GET /health` - Health check
- `POST /upload/pdf` - PDF document upload
- `POST /api/process/urls` - URL processing
- `GET /jobs` - List processing jobs

## Integration Notes
The frontend expects:
- `REACT_APP_API_URL` environment variable set to API Gateway URL
- CORS headers configured (already set in FastAPI)
- Authentication headers (future enhancement)