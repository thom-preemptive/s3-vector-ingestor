#!/bin/bash

# Create S3 bucket with proper CORS configuration

BUCKET_NAME="agent2-ingestor-bucket-us-east-1"
REGION="us-east-1"

echo "🪣 Creating S3 bucket with CORS configuration"
echo "=============================================="
echo "Bucket: $BUCKET_NAME"
echo "Region: $REGION"
echo ""

# Create the bucket (us-east-1 doesn't need LocationConstraint)
echo "Creating bucket..."
aws s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --region "$REGION" 2>&1

if [ $? -eq 0 ] || [[ $(aws s3api head-bucket --bucket "$BUCKET_NAME" 2>&1) == "" ]]; then
    echo "✅ Bucket exists or was created"
else
    echo "❌ Failed to create bucket"
    exit 1
fi

# Apply CORS configuration
echo ""
echo "Applying CORS configuration..."
cat > /tmp/s3-cors-config.json << 'EOF'
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag", "x-amz-request-id", "x-amz-server-side-encryption"],
      "MaxAgeSeconds": 3000
    }
  ]
}
EOF

aws s3api put-bucket-cors \
    --bucket "$BUCKET_NAME" \
    --cors-configuration file:///tmp/s3-cors-config.json \
    --region "$REGION"

if [ $? -eq 0 ]; then
    echo "✅ CORS configuration applied"
else
    echo "❌ Failed to apply CORS"
    rm /tmp/s3-cors-config.json
    exit 1
fi

# Enable versioning (optional but recommended)
echo ""
echo "Enabling versioning..."
aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled \
    --region "$REGION"

# Verify CORS configuration
echo ""
echo "Verifying CORS configuration..."
aws s3api get-bucket-cors --bucket "$BUCKET_NAME" --region "$REGION"

echo ""
echo "✅ S3 bucket is ready for file uploads!"
echo ""
echo "Bucket name: $BUCKET_NAME"
echo "Region: $REGION"
echo "CORS: Enabled for all origins"

# Clean up
rm /tmp/s3-cors-config.json
