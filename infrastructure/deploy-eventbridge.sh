#!/bin/bash

# Deploy EventBridge infrastructure for agent2_ingestor

set -e

ENVIRONMENT="dev"
REGION="us-east-1"
STACK_NAME="agent2-ingestor-eventbridge-${ENVIRONMENT}"

echo "🚀 Deploying EventBridge infrastructure..."

# Get the Lambda function ARN from the backend stack
echo "📋 Getting Lambda function ARN..."
LAMBDA_ARN=$(aws cloudformation describe-stacks \
  --stack-name agent2-ingestor-backend-dev \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`Agent2IngestorAPIArn`].OutputValue' \
  --output text 2>/dev/null || echo "")

if [ -z "$LAMBDA_ARN" ]; then
  echo "⚠️  Lambda ARN not found in stack outputs. Looking up function directly..."
  LAMBDA_ARN=$(aws lambda get-function \
    --function-name agent2-ingestor-api-${ENVIRONMENT} \
    --region $REGION \
    --query 'Configuration.FunctionArn' \
    --output text)
fi

echo "✓ Lambda ARN: $LAMBDA_ARN"

# Deploy CloudFormation stack
echo "📦 Deploying CloudFormation stack: $STACK_NAME"

aws cloudformation deploy \
  --template-file eventbridge-setup.yaml \
  --stack-name $STACK_NAME \
  --parameter-overrides \
    Environment=$ENVIRONMENT \
    S3BucketName=agent2-ingestor-bucket-us-east-1 \
    ProcessorLambdaArn=$LAMBDA_ARN \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

echo ""
echo "✅ EventBridge infrastructure deployed successfully!"
echo ""

# Get outputs
EVENT_BUS_NAME=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`EventBusName`].OutputValue' \
  --output text)

EVENT_BUS_ARN=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`EventBusArn`].OutputValue' \
  --output text)

POLICY_ARN=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`EventBridgePutEventsPolicyArn`].OutputValue' \
  --output text)

echo "📋 Stack Outputs:"
echo "  Event Bus Name: $EVENT_BUS_NAME"
echo "  Event Bus ARN: $EVENT_BUS_ARN"
echo "  Put Events Policy ARN: $POLICY_ARN"
echo ""

# Attach the EventBridge policy to the API Lambda role
echo "🔗 Attaching EventBridge policy to Lambda role..."
ROLE_NAME=$(aws lambda get-function \
  --function-name agent2-ingestor-api-${ENVIRONMENT} \
  --region $REGION \
  --query 'Configuration.Role' \
  --output text | awk -F'/' '{print $NF}')

aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn $POLICY_ARN \
  --region $REGION || echo "⚠️  Policy may already be attached"

echo ""
echo "✅ Setup complete! Event bus: $EVENT_BUS_NAME"
echo ""
echo "💡 Next steps:"
echo "   1. Update backend environment variable: EVENT_BUS_NAME=$EVENT_BUS_NAME"
echo "   2. Redeploy backend with: cd ../backend && sam build && sam deploy"
