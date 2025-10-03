#!/bin/bash

# Configure CORS on the S3 bucket to allow direct uploads from browser

BUCKET_NAME="agent2-ingestor-bucket-us-east-1"
REGION="us-east-1"

echo "🔧 Configuring CORS for S3 bucket: $BUCKET_NAME"
echo "================================================"

# Create CORS configuration JSON
cat > /tmp/s3-cors-config.json << 'EOF'
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag", "x-amz-request-id"],
      "MaxAgeSeconds": 3000
    }
  ]
}
EOF

echo "Applying CORS configuration..."
aws s3api put-bucket-cors \
    --bucket "$BUCKET_NAME" \
    --cors-configuration file:///tmp/s3-cors-config.json \
    --region "$REGION"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ S3 CORS configuration applied successfully!"
    echo ""
    echo "Verifying configuration..."
    aws s3api get-bucket-cors --bucket "$BUCKET_NAME" --region "$REGION"
    echo ""
    echo "✅ S3 bucket is now configured to accept uploads from the browser!"
else
    echo ""
    echo "❌ Failed to configure S3 CORS"
    exit 1
fi

# Clean up
rm /tmp/s3-cors-config.json
