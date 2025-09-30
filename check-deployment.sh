#!/bin/bash

# Check Amplify deployment status
APP_ID="dn1hdu83qdv9u"
BRANCH="dev"
REGION="us-east-1"

echo "🚀 Checking Amplify Deployment Status"
echo "======================================"
echo "App ID: $APP_ID"
echo "Branch: $BRANCH"
echo "Region: $REGION"
echo ""

# Get the latest job
echo "📊 Latest Jobs:"
aws amplify list-jobs --app-id $APP_ID --branch-name $BRANCH --region $REGION --max-items 3

echo ""
echo "🌐 Branch Status:"
aws amplify get-branch --app-id $APP_ID --branch-name $BRANCH --region $REGION --query 'branch.[displayName,stage,environmentVariables]' --output table

echo ""
echo "🔗 App URL:"
aws amplify get-app --app-id $APP_ID --region $REGION --query 'app.defaultDomain' --output text

echo ""
echo "📱 Dev Branch URL:"
echo "https://dev.$(aws amplify get-app --app-id $APP_ID --region $REGION --query 'app.defaultDomain' --output text)"