# AWS Amplify Deployment Guide for agent2_ingestor

## Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Git repository** (GitHub/GitLab/CodeCommit) 
3. **AWS Account** with permissions for:
   - Amplify
   - S3
   - DynamoDB
   - Lambda
   - API Gateway
   - Cognito
   - Textract
   - Bedrock

## Step 1: Prepare Repository

Your repository is already configured with:
- ✅ `amplify.yml` build configuration
- ✅ Frontend React application in `/frontend`
- ✅ Backend FastAPI application in `/backend`
- ✅ Infrastructure templates in `/infrastructure`

## Step 2: Deploy Infrastructure

Before deploying the Amplify app, deploy the required AWS infrastructure:

```bash
# Set environment variables
export AWS_REGION=us-east-1
export S3_BUCKET=agent2-ingestor-bucket-us-east-1
export DYNAMODB_TABLE=agent2-ingestor-jobs
export COGNITO_USER_POOL_ID=your-user-pool-id
export COGNITO_CLIENT_ID=your-client-id

# Deploy S3 and basic infrastructure
cd infrastructure
python setup_aws.py

# Deploy queue infrastructure
python deploy_queue_infrastructure.py --environment prod --s3-bucket agent2-ingestor-bucket-us-east-1

# Deploy orchestration (Lambda functions)
python deploy_orchestration.py
```

## Step 3: Create Amplify App

### Option A: AWS Console (Recommended)

1. **Go to AWS Amplify Console** in us-east-1 region
2. **Click "Host web app"**
3. **Select your Git provider** (GitHub/GitLab/CodeCommit)
4. **Choose your repository** containing agent2_ingestor
5. **Configure build settings**:
   - Branch: `main` (or your primary branch)
   - App name: `agent2-ingestor`
   - Environment: `prod`

### Option B: AWS CLI

```bash
# Create Amplify app
aws amplify create-app \
  --name "agent2-ingestor" \
  --description "Document processing system with vector sidecars" \
  --repository "https://github.com/your-username/agent2_ingestor" \
  --platform "WEB" \
  --region us-east-1

# Create branch
aws amplify create-branch \
  --app-id <app-id-from-previous-command> \
  --branch-name main \
  --description "Main production branch"

# Start deployment
aws amplify start-job \
  --app-id <app-id> \
  --branch-name main \
  --job-type RELEASE
```

## Step 4: Configure Environment Variables

In the Amplify Console, add these environment variables:

### Frontend Environment Variables
```
REACT_APP_API_URL=https://your-api-gateway-url
REACT_APP_AWS_REGION=us-east-1
REACT_APP_COGNITO_USER_POOL_ID=your-user-pool-id
REACT_APP_COGNITO_CLIENT_ID=your-client-id
```

### Backend Environment Variables
```
AWS_REGION=us-east-1
S3_BUCKET=agent2-ingestor-bucket-us-east-1
DYNAMODB_TABLE=agent2-ingestor-jobs
COGNITO_USER_POOL_ID=your-user-pool-id
COGNITO_CLIENT_ID=your-client-id
TEXTRACT_REGION=us-east-1
BEDROCK_REGION=us-east-1
```

## Step 5: Configure Custom Domain (Optional)

1. **In Amplify Console**, go to "Domain management"
2. **Add domain** (e.g., agent2-ingestor.your-domain.com)
3. **Configure DNS** as instructed by Amplify
4. **Wait for SSL certificate** provisioning

## Step 6: Set up Backend API

The backend FastAPI application can be deployed as:

### Option A: Lambda Function (Serverless)
```bash
# Package and deploy FastAPI as Lambda
cd backend
pip install -r requirements.txt -t ./package
cd package
zip -r ../agent2-ingestor-api.zip .
cd ..
zip -g agent2-ingestor-api.zip *.py

# Deploy to Lambda
aws lambda create-function \
  --function-name agent2-ingestor-api \
  --runtime python3.9 \
  --role arn:aws:iam::your-account:role/lambda-execution-role \
  --handler main.handler \
  --zip-file fileb://agent2-ingestor-api.zip
```

### Option B: EC2/ECS Container
```bash
# Create Dockerfile for FastAPI
# Deploy to ECS or EC2 instance
# Configure load balancer
```

## Step 7: Configure API Gateway

1. **Create REST API** in API Gateway
2. **Configure proxy integration** to backend
3. **Enable CORS** for frontend domain
4. **Deploy API** to production stage
5. **Update frontend environment** with API URL

## Step 8: Test Deployment

### Frontend Testing
1. **Visit Amplify URL** (provided in console)
2. **Test user authentication** (Cognito)
3. **Test document upload** functionality
4. **Test dashboard** and monitoring

### Backend Testing
```bash
# Test API endpoints
curl https://your-api-gateway-url/health
curl https://your-api-gateway-url/docs
```

### End-to-End Testing
1. **Upload a PDF** through frontend
2. **Process a URL** through frontend  
3. **Monitor job status** in dashboard
4. **Check S3 bucket** for processed files
5. **Verify DynamoDB** job tracking

## Step 9: Monitoring and Logs

### CloudWatch Logs
- Amplify build logs
- Lambda function logs
- API Gateway logs

### CloudWatch Metrics
- Amplify performance metrics
- Lambda execution metrics
- DynamoDB read/write metrics

### Custom Monitoring
- Use the built-in dashboard at `/dashboard/overview`
- Monitor system health at `/dashboard/health`

## Deployment URLs

After successful deployment:

- **Frontend**: `https://main.d1234567890.amplifyapp.com/`
- **API Documentation**: `https://your-api-gateway-url/docs`
- **System Dashboard**: `https://main.d1234567890.amplifyapp.com/dashboard`

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check `amplify.yml` configuration
   - Verify Node.js and Python versions
   - Check environment variables

2. **API Connection Issues**
   - Verify CORS configuration
   - Check API Gateway deployment
   - Validate environment variables

3. **Authentication Issues**
   - Verify Cognito configuration
   - Check user pool settings
   - Validate client app settings

### Debug Commands

```bash
# Check Amplify app status
aws amplify get-app --app-id <app-id>

# List branches
aws amplify list-branches --app-id <app-id>

# Get job details
aws amplify get-job --app-id <app-id> --branch-name main --job-id <job-id>
```

## Security Considerations

1. **Environment Variables**: Use Amplify environment variables, not hardcoded values
2. **IAM Roles**: Follow principle of least privilege
3. **CORS**: Configure restrictive CORS policies
4. **Authentication**: Use Cognito for user authentication
5. **API Keys**: Use AWS IAM for API authentication

## Cost Optimization

1. **S3**: Use lifecycle policies for old documents
2. **DynamoDB**: Use on-demand pricing for variable workloads
3. **Lambda**: Optimize function memory and timeout
4. **Amplify**: Monitor build minutes usage

## Next Steps

After successful deployment:

1. **Set up monitoring alerts** in CloudWatch
2. **Configure backup strategies** for S3 and DynamoDB
3. **Implement CI/CD pipeline** improvements
4. **Add custom domain** and SSL certificate
5. **Scale infrastructure** based on usage patterns

Your agent2_ingestor is now ready for production deployment on AWS Amplify!