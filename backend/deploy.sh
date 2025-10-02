#!/bin/bash

# agent2_ingestor Backend API Deployment Script
# This script deploys the FastAPI backend to AWS Lambda using SAM

set -e

echo "🚀 agent2_ingestor - Backend API Deployment"
echo "=========================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

# Check SAM CLI
if ! command -v sam &> /dev/null; then
    echo "❌ SAM CLI not found. Please install SAM CLI first."
    echo "   Visit: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ Prerequisites check completed"

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
ENVIRONMENT=${ENVIRONMENT:-dev}
STACK_NAME="agent2-ingestor-backend-${ENVIRONMENT}"

echo ""
echo "📝 Configuration:"
echo "   Environment: $ENVIRONMENT"
echo "   Region: $AWS_REGION"
echo "   Stack Name: $STACK_NAME"

echo ""
read -p "🤔 Do you want to continue with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

echo ""
echo "🔧 Step 1: Building SAM application..."
sam build

echo ""
echo "🚀 Step 2: Deploying to AWS..."
sam deploy \
    --stack-name "$STACK_NAME" \
    --capabilities CAPABILITY_IAM \
    --region "$AWS_REGION" \
    --parameter-overrides Environment="$ENVIRONMENT" \
    --resolve-s3 \
    --no-confirm-changeset \
    --no-fail-on-empty-changeset

echo ""
echo "📊 Step 3: Getting deployment information..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text)

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 API Endpoint: $API_URL"
echo ""
echo "📝 Next steps:"
echo "1. Test the API: curl $API_URL/health"
echo "2. Update frontend environment variables with the API URL"
echo "3. Test the integration"
echo ""