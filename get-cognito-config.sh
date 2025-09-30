#!/bin/bash

# Script to get Cognito User Pool and Client IDs for agent2_ingestor environments
# Run this script to get the actual IDs to configure in Amplify

echo "🔍 Finding Cognito User Pools for agent2_ingestor..."
echo "=================================================="

REGION="us-east-1"

# Function to get user pool details
get_user_pool_details() {
    local pool_name=$1
    local env=$2
    
    echo ""
    echo "🔎 Looking for user pool: $pool_name"
    
    # Get user pool ID
    USER_POOL_ID=$(aws cognito-idp list-user-pools \
        --max-results 50 \
        --region $REGION \
        --query "UserPools[?Name=='$pool_name'].Id" \
        --output text 2>/dev/null)
    
    if [ -n "$USER_POOL_ID" ] && [ "$USER_POOL_ID" != "None" ]; then
        echo "✅ Found User Pool ID: $USER_POOL_ID"
        
        # Get client ID(s)
        CLIENT_IDS=$(aws cognito-idp list-user-pool-clients \
            --user-pool-id $USER_POOL_ID \
            --region $REGION \
            --query "UserPoolClients[*].ClientId" \
            --output text 2>/dev/null)
        
        if [ -n "$CLIENT_IDS" ] && [ "$CLIENT_IDS" != "None" ]; then
            echo "✅ Found Client ID(s): $CLIENT_IDS"
            
            # Get the first client ID (assuming there's one per pool)
            FIRST_CLIENT_ID=$(echo $CLIENT_IDS | awk '{print $1}')
            
            echo ""
            echo "📋 Environment Variables for $env environment:"
            echo "REACT_APP_COGNITO_USER_POOL_ID_${env^^}=$USER_POOL_ID"
            echo "REACT_APP_COGNITO_CLIENT_ID_${env^^}=$FIRST_CLIENT_ID"
            
            # Store for summary
            eval "USER_POOL_${env^^}=$USER_POOL_ID"
            eval "CLIENT_ID_${env^^}=$FIRST_CLIENT_ID"
        else
            echo "❌ No client apps found for this user pool"
            echo "   You may need to create a client app for: $USER_POOL_ID"
        fi
    else
        echo "❌ User pool '$pool_name' not found"
        echo "   You may need to create it first"
    fi
}

# Check each environment
get_user_pool_details "agent2-ingestor-dev" "dev"
get_user_pool_details "agent2-ingestor-test" "test"  
get_user_pool_details "agent2-ingestor-main" "main"

echo ""
echo "🚀 Summary - Amplify Environment Variables to Set:"
echo "=================================================="
echo ""
echo "For DEV branch:"
if [ -n "$USER_POOL_DEV" ]; then
    echo "REACT_APP_COGNITO_USER_POOL_ID_DEV=$USER_POOL_DEV"
    echo "REACT_APP_COGNITO_CLIENT_ID_DEV=$CLIENT_ID_DEV"
else
    echo "❌ DEV environment not configured"
fi

echo ""
echo "For TEST branch:"
if [ -n "$USER_POOL_TEST" ]; then
    echo "REACT_APP_COGNITO_USER_POOL_ID_TEST=$USER_POOL_TEST"
    echo "REACT_APP_COGNITO_CLIENT_ID_TEST=$CLIENT_ID_TEST"
else
    echo "❌ TEST environment not configured"
fi

echo ""
echo "For MAIN branch:"
if [ -n "$USER_POOL_MAIN" ]; then
    echo "REACT_APP_COGNITO_USER_POOL_ID_MAIN=$USER_POOL_MAIN"
    echo "REACT_APP_COGNITO_CLIENT_ID_MAIN=$CLIENT_ID_MAIN"
else
    echo "❌ MAIN environment not configured"
fi

echo ""
echo "📝 Next Steps:"
echo "1. Copy the environment variables above"
echo "2. Go to AWS Amplify Console → App Settings → Environment Variables"
echo "3. Add each variable for the appropriate branch/environment"
echo "4. Redeploy the application"
echo ""
echo "💡 Tip: You can also set these via AWS CLI:"
echo "aws amplify put-backend-environment --app-id <app-id> --environment-name <env> ..."