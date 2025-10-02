#!/bin/bash

# Set the correct API URL environment variable in Amplify
# This fixes the "https://your-api-url" placeholder issue

echo "🔧 Fixing Amplify Environment Variables"
echo "========================================"

APP_ID="dn1hdu83qdv9u"
BRANCH="dev"
REGION="us-east-1"

# The correct API endpoint
API_URL="https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev"

# Updated Cognito values from your current setup
USER_POOL_ID="us-east-1_Yk8Yt64uE"
CLIENT_ID="6hcundvt29da9ap8ji973h1pqq"

echo "Setting environment variables for branch: $BRANCH"
echo "API URL: $API_URL"
echo ""

# Update the branch with ALL environment variables including the API URL
aws amplify update-branch \
    --app-id "$APP_ID" \
    --branch-name "$BRANCH" \
    --environment-variables \
        REACT_APP_API_URL="$API_URL" \
        REACT_APP_COGNITO_USER_POOL_ID="$USER_POOL_ID" \
        REACT_APP_COGNITO_CLIENT_ID="$CLIENT_ID" \
        REACT_APP_AWS_REGION="$REGION" \
        AWS_BRANCH="$BRANCH" \
        REACT_APP_AMPLIFY_ENV="$BRANCH" \
        CI="true" \
        GENERATE_SOURCEMAP="false" \
        TSC_COMPILE_ON_ERROR="true" \
        ESLINT_NO_DEV_ERRORS="true" \
    --region "$REGION"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Environment variables updated successfully!"
    echo ""
    echo "📋 Triggering new deployment..."
    
    # Trigger a new build to use the updated environment variables
    aws amplify start-job \
        --app-id "$APP_ID" \
        --branch-name "$BRANCH" \
        --job-type RELEASE \
        --region "$REGION"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Deployment triggered successfully!"
        echo ""
        echo "🎉 Once the build completes:"
        echo "   1. The API URL will be correct"
        echo "   2. Uploads should return real job IDs"
        echo "   3. Jobs page should display data"
        echo ""
        echo "Check Amplify Console for build progress:"
        echo "https://us-east-1.console.aws.amazon.com/amplify/home?region=us-east-1#/$APP_ID"
    else
        echo ""
        echo "❌ Failed to trigger deployment"
    fi
else
    echo ""
    echo "❌ Failed to update environment variables"
fi
