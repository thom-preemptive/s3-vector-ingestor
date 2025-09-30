#!/bin/bash

# Script to set Amplify environment variables via AWS CLI
# This allows you to set variables for specific branches

APP_ID="dn1hdu83qdv9u"  # Your Amplify app ID
REGION="us-east-1"

echo "🔧 Setting Amplify Environment Variables via AWS CLI"
echo "===================================================="

# Function to set environment variables for a branch
set_branch_env_vars() {
    local branch=$1
    local user_pool_id=$2
    local client_id=$3
    
    echo ""
    echo "Setting environment variables for $branch branch..."
    
    # Set the environment variables
    aws amplify update-branch \
        --app-id $APP_ID \
        --branch-name $branch \
        --environment-variables \
            "REACT_APP_COGNITO_USER_POOL_ID_${branch^^}=$user_pool_id" \
            "REACT_APP_COGNITO_CLIENT_ID_${branch^^}=$client_id" \
            "AWS_BRANCH=$branch" \
            "REACT_APP_AMPLIFY_ENV=$branch" \
            "REACT_APP_AWS_REGION=us-east-1" \
        --region $REGION
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully set environment variables for $branch"
    else
        echo "❌ Failed to set environment variables for $branch"
    fi
}

# Set variables for each environment
echo "Setting up environment variables for all branches..."

# DEV environment
set_branch_env_vars "dev" "us-east-1_ZXccV9Ntq" "3u5hedl2mp0bvg5699l16dj4oe"

# TEST environment (uncomment when you create the test branch)
# set_branch_env_vars "test" "us-east-1_epXBgyusk" "7h6q69gsuoo77200knu88dmoe4"

# MAIN environment (uncomment when you create the main branch)
# set_branch_env_vars "main" "us-east-1_KD9IBTRJl" "4eq1gmn394e8ct1gpjra89vgak"

echo ""
echo "🎉 Environment variable setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Verify the variables were set correctly"
echo "2. Trigger a new deployment to test"
echo ""
echo "🔍 To verify, run:"
echo "aws amplify get-branch --app-id $APP_ID --branch-name dev --region $REGION"