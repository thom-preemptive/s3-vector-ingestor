#!/bin/bash

# Script to create environment-specific S3 buckets for agent2_ingestor
# Each environment (dev, test, main) gets its own isolated S3 bucket

set -e

REGION="us-east-1"
ENVIRONMENTS=("dev" "test" "main")

# CORS configuration
CORS_CONFIG='{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag"],
      "MaxAgeSeconds": 3000
    }
  ]
}'

echo "🪣 Creating environment-specific S3 buckets..."
echo "=============================================="

for ENV in "${ENVIRONMENTS[@]}"; do
    BUCKET_NAME="agent2-ingestor-bucket-${ENV}-us-east-1"
    
    echo ""
    echo "📦 Processing environment: $ENV"
    echo "   Bucket name: $BUCKET_NAME"
    
    # Check if bucket exists
    if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
        echo "   ✅ Bucket already exists"
    else
        echo "   🔨 Creating bucket..."
        aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$REGION" \
            2>/dev/null || echo "   ⚠️  Bucket creation failed (may already exist)"
    fi
    
    # Configure CORS
    echo "   🌐 Configuring CORS..."
    echo "$CORS_CONFIG" | aws s3api put-bucket-cors \
        --bucket "$BUCKET_NAME" \
        --cors-configuration file:///dev/stdin
    
    # Enable versioning (recommended for document storage)
    echo "   📋 Enabling versioning..."
    aws s3api put-bucket-versioning \
        --bucket "$BUCKET_NAME" \
        --versioning-configuration Status=Enabled
    
    # Set encryption
    echo "   🔒 Enabling encryption..."
    aws s3api put-bucket-encryption \
        --bucket "$BUCKET_NAME" \
        --server-side-encryption-configuration '{
          "Rules": [
            {
              "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
              }
            }
          ]
        }'
    
    echo "   ✅ Bucket $BUCKET_NAME configured successfully"
done

echo ""
echo "=============================================="
echo "✅ All S3 buckets created and configured!"
echo ""
echo "📊 Bucket Summary:"
echo "   • agent2-ingestor-bucket-dev-us-east-1"
echo "   • agent2-ingestor-bucket-test-us-east-1"
echo "   • agent2-ingestor-bucket-main-us-east-1"
echo ""
echo "🔍 Verify buckets:"
for ENV in "${ENVIRONMENTS[@]}"; do
    BUCKET_NAME="agent2-ingestor-bucket-${ENV}-us-east-1"
    echo "   aws s3 ls s3://$BUCKET_NAME/"
done
