#!/bin/bash

# agent2_ingestor AWS Amplify Deployment Script
# This script helps deploy the application to AWS Amplify

set -e

echo "🚀 agent2_ingestor - AWS Amplify Deployment"
echo "============================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI first."
    echo "   Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 16+ first."
    exit 1
fi

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install npm first."
    exit 1
fi

echo "✅ Prerequisites check completed"

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
APP_NAME="agent2-ingestor"
REPOSITORY_URL=${REPOSITORY_URL:-""}
BRANCH_NAME=${BRANCH_NAME:-main}

echo ""
echo "📝 Configuration:"
echo "   App Name: $APP_NAME"
echo "   Region: $AWS_REGION"
echo "   Branch: $BRANCH_NAME"

if [ -z "$REPOSITORY_URL" ]; then
    echo ""
    echo "⚠️  Repository URL not provided. You'll need to connect manually in the AWS Console."
    echo "   Set REPOSITORY_URL environment variable to auto-connect (e.g., https://github.com/user/repo)"
fi

echo ""
read -p "🤔 Do you want to continue with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

echo ""
echo "🔧 Step 1: Preparing frontend build..."
cd frontend

# Install dependencies
echo "   Installing npm dependencies..."
npm ci

# Create production environment file
echo "   Creating production environment configuration..."
if [ ! -f .env.production ]; then
    cp .env.production.example .env.production
    echo "   ⚠️  Created .env.production from example. Please update with your actual values."
fi

# Test build
echo "   Testing frontend build..."
npm run build
echo "   ✅ Frontend build test successful"

cd ..

echo ""
echo "🔧 Step 2: Creating Amplify app..."

# Create Amplify app
APP_ID=$(aws amplify create-app \
    --name "$APP_NAME" \
    --description "Document processing system with vector sidecars" \
    --platform "WEB" \
    --region "$AWS_REGION" \
    --query 'app.appId' \
    --output text)

if [ $? -eq 0 ]; then
    echo "   ✅ Amplify app created successfully"
    echo "   📝 App ID: $APP_ID"
else
    echo "   ❌ Failed to create Amplify app"
    exit 1
fi

echo ""
echo "🔧 Step 3: Configuring environment variables..."

# Set environment variables for Amplify
aws amplify put-backend-environment \
    --app-id "$APP_ID" \
    --environment-name "prod" \
    --deployment-artifacts '{}' \
    --region "$AWS_REGION" || true

echo "   ✅ Environment configuration completed"

echo ""
echo "🔧 Step 4: Setting up branch..."

# Create branch (if repository URL is provided)
if [ ! -z "$REPOSITORY_URL" ]; then
    echo "   Connecting repository: $REPOSITORY_URL"
    
    aws amplify create-branch \
        --app-id "$APP_ID" \
        --branch-name "$BRANCH_NAME" \
        --description "Main production branch" \
        --region "$AWS_REGION"
    
    if [ $? -eq 0 ]; then
        echo "   ✅ Branch created and connected successfully"
    else
        echo "   ⚠️  Branch creation failed. You may need to connect manually."
    fi
else
    echo "   ⚠️  Skipping automatic repository connection"
fi

echo ""
echo "🎉 Deployment preparation completed!"
echo ""
echo "📋 Next steps:"
echo "1. 🌐 Visit AWS Amplify Console: https://console.aws.amazon.com/amplify/apps/$APP_ID"
echo "2. 🔗 Connect your repository (if not done automatically)"
echo "3. ⚙️  Configure environment variables:"
echo "   - REACT_APP_API_URL=https://your-api-gateway-url"
echo "   - REACT_APP_COGNITO_USER_POOL_ID=your-user-pool-id"
echo "   - REACT_APP_COGNITO_CLIENT_ID=your-client-id"
echo "4. 🚀 Deploy the app"
echo "5. 🧪 Test the deployment"
echo ""
echo "📖 For detailed instructions, see: AMPLIFY_DEPLOYMENT.md"
echo ""
echo "🔗 Amplify Console: https://console.aws.amazon.com/amplify/apps/$APP_ID"
echo "📱 App ID: $APP_ID"
echo ""

# Save configuration for future reference
cat > amplify-config.json << EOF
{
  "appId": "$APP_ID",
  "appName": "$APP_NAME",
  "region": "$AWS_REGION",
  "branchName": "$BRANCH_NAME",
  "repositoryUrl": "$REPOSITORY_URL",
  "createdAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo "💾 Configuration saved to amplify-config.json"
echo ""
echo "✨ Ready for AWS Amplify deployment!"