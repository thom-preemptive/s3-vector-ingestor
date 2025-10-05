#!/bin/bash

# Script to initialize the folder structure in test and main S3 buckets
# Creates empty manifest.json files for each environment

set -e

REGION="us-east-1"
ENVIRONMENTS=("test" "main")

# Create empty manifest template
EMPTY_MANIFEST='{
  "version": "1.0",
  "created_at": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
  "documents": [],
  "document_count": 0,
  "last_updated": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'"
}'

echo "📁 Initializing S3 bucket structure for test and main environments"
echo "=================================================================="

for ENV in "${ENVIRONMENTS[@]}"; do
    BUCKET_NAME="agent2-ingestor-bucket-${ENV}-us-east-1"
    
    echo ""
    echo "🔧 Initializing: $ENV environment"
    echo "   Bucket: $BUCKET_NAME"
    
    # Create empty manifest.json
    echo "   📄 Creating empty manifest.json..."
    echo "$EMPTY_MANIFEST" | aws s3 cp - "s3://${BUCKET_NAME}/manifest.json" \
        --content-type "application/json"
    
    # Note: S3 folders don't need to be created explicitly - they're virtual
    # They will be created automatically when files are uploaded to those paths
    # However, we can create placeholder files to make the structure visible
    
    echo "   📂 Folder structure will be created automatically on first upload:"
    echo "      • documents/ (created when first document is processed)"
    echo "      • sidecars/ (created when first sidecar is uploaded)"
    echo "      • uploads/ (created when first file is uploaded)"
    
    echo "   ✅ $ENV environment initialized"
done

echo ""
echo "=================================================================="
echo "✅ Bucket initialization complete!"
echo ""
echo "📊 Verify initialization:"
for ENV in "${ENVIRONMENTS[@]}"; do
    BUCKET_NAME="agent2-ingestor-bucket-${ENV}-us-east-1"
    echo "   aws s3 ls s3://$BUCKET_NAME/"
done
echo ""
echo "📝 Note: The folders (documents/, sidecars/, uploads/) will be created"
echo "   automatically when the first document is processed in each environment."
