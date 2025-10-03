#!/bin/bash

# Test EventBridge integration
# This sends a test event to EventBridge to verify the flow works

EVENT_BUS_NAME="agent2-ingestor-events-dev"
REGION="us-east-1"

echo "🧪 Testing EventBridge integration..."
echo ""

# Create test event payload
TEST_EVENT=$(cat <<EOF
[
  {
    "Source": "agent2.ingestor",
    "DetailType": "Document Processing Required",
    "Detail": "{\"job_id\": \"test-job-$(date +%s)\", \"user_id\": \"test-user\", \"job_name\": \"EventBridge Test\", \"files\": [{\"file_key\": \"test/file.pdf\", \"filename\": \"test.pdf\"}], \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%S)Z\", \"action\": \"process_documents\"}",
    "EventBusName": "$EVENT_BUS_NAME"
  }
]
EOF
)

# Send test event
echo "📤 Sending test event to EventBridge..."
RESPONSE=$(aws events put-events --entries "$TEST_EVENT" --region $REGION)

echo "Response: $RESPONSE"
echo ""

# Check if successful
FAILED_COUNT=$(echo $RESPONSE | jq -r '.FailedEntryCount')

if [ "$FAILED_COUNT" == "0" ]; then
    echo "✅ Test event sent successfully!"
    echo ""
    echo "💡 Check Lambda logs to verify processing:"
    echo "   aws logs tail /aws/lambda/agent2-ingestor-api-dev --follow --region $REGION"
else
    echo "❌ Failed to send test event"
    echo "Failures: $(echo $RESPONSE | jq -r '.Entries')"
fi
