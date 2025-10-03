# Troubleshooting Guide: Document Viewing Features

## Common Issues and Solutions

### Issue 1: HTTP 404 Error on Documents Page

**Symptom**: Documents page shows "HTTP error! status: 404"

**Root Cause**: FastAPI route ordering issue. Dynamic path parameters (`/documents/{document_id}`) were defined before specific routes (`/documents/search`), causing FastAPI to match "search" as a document ID.

**Solution**: Routes must be ordered from most specific to least specific:
```python
# ✅ CORRECT ORDER
@app.get("/documents/search")          # Most specific - exact match
@app.get("/documents/manifest")        # Specific - exact match
@app.get("/documents/stats")           # Specific - exact match
@app.get("/documents/{document_id}/download")  # Specific with param
@app.get("/documents/{document_id}")   # Dynamic parameter
@app.get("/documents")                 # Base route

# ❌ INCORRECT ORDER
@app.get("/documents/{document_id}")   # This would catch "search" as ID
@app.get("/documents/search")          # Never reached!
```

**Files Modified**: `backend/main.py`

**Deployment Required**: Yes - backend must be redeployed after fixing route order

---

### Issue 2: No Documents Available (After Successful Upload)

**Symptom**: Documents page loads but shows "No documents available"

**Possible Causes**:
1. **No completed jobs** - Documents only appear after job status = "completed"
2. **Empty manifest** - manifest.json doesn't exist or has no documents
3. **S3 permissions** - Lambda can't read manifest.json

**Diagnostic Steps**:

1. Check if manifest exists:
```bash
aws s3 ls s3://agent2-ingestor-bucket-us-east-1/manifest.json
```

2. Download and inspect manifest:
```bash
aws s3 cp s3://agent2-ingestor-bucket-us-east-1/manifest.json - | jq '.'
```

3. Check job status in DynamoDB:
```bash
aws dynamodb scan --table-name document-jobs \
  --filter-expression "#s = :status" \
  --expression-attribute-names '{"#s":"status"}' \
  --expression-attribute-values '{":status":{"S":"completed"}}' \
  --region us-east-1
```

4. Check CloudWatch logs:
```bash
aws logs tail /aws/lambda/agent2-ingestor-api-dev --follow --region us-east-1
```

**Solutions**:
- Wait for job to complete (check Jobs page)
- Upload a document if none exist
- Verify S3 bucket permissions in Lambda IAM role
- Check document_processor.py is updating manifest correctly

---

### Issue 3: Search Not Working

**Symptom**: Search bar doesn't return results, or shows error

**Possible Causes**:
1. Search query too short (< 2 characters)
2. API endpoint returning 404 (route ordering issue)
3. No documents in manifest
4. Network/CORS error

**Diagnostic Steps**:

1. Check browser console for errors:
   - Open DevTools (F12)
   - Look for red errors in Console tab
   - Check Network tab for failed requests

2. Test API directly:
```bash
# Get auth token from browser (Application > Cookies > idToken)
TOKEN="your-id-token-here"

curl -H "Authorization: Bearer $TOKEN" \
  "https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev/documents/search?q=test"
```

3. Verify documents exist:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev/documents/manifest"
```

**Solutions**:
- Ensure query is at least 2 characters
- Fix route ordering in backend (see Issue 1)
- Upload documents if none exist
- Check CORS configuration on API Gateway

---

### Issue 4: Document Viewer Shows "Document Not Found"

**Symptom**: Clicking "View" on a document shows error "Document not found"

**Possible Causes**:
1. Document ID doesn't exist in manifest
2. S3 files were deleted but manifest not updated
3. Incorrect document_id in URL

**Diagnostic Steps**:

1. Check document exists in manifest:
```bash
aws s3 cp s3://agent2-ingestor-bucket-us-east-1/manifest.json - | \
  jq '.documents[] | select(.document_id=="YOUR_DOC_ID")'
```

2. Verify S3 files exist:
```bash
# Replace with actual keys from manifest
aws s3 ls s3://agent2-ingestor-bucket-us-east-1/documents/USER_ID/JOB_ID/
```

3. Check API response:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev/documents/YOUR_DOC_ID"
```

**Solutions**:
- Verify document_id is correct
- Check S3 files haven't been deleted
- Re-process document if files are missing
- Validate manifest integrity via `/documents/manifest` endpoint

---

### Issue 5: Markdown Content Not Rendering

**Symptom**: Document viewer shows blank content area or raw markdown text

**Possible Causes**:
1. react-markdown not installed
2. Markdown content is null/empty
3. S3 file doesn't exist
4. JavaScript error in browser

**Diagnostic Steps**:

1. Check react-markdown installed:
```bash
cd frontend
npm list react-markdown
```

2. Check browser console for errors

3. Verify markdown content in API response:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev/documents/YOUR_DOC_ID" | \
  jq '.markdown_content'
```

**Solutions**:
- Install react-markdown: `npm install react-markdown`
- Rebuild frontend: `npm run build`
- Check S3 file exists and has content
- Verify DocumentProcessor is generating markdown correctly

---

### Issue 6: Download Fails

**Symptom**: Clicking download button shows error or nothing happens

**Possible Causes**:
1. S3 file doesn't exist
2. Lambda doesn't have S3 read permissions
3. Browser blocking download
4. API returning 404/500

**Diagnostic Steps**:

1. Check browser Network tab for failed request

2. Test download API:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev/documents/YOUR_DOC_ID/download?format=markdown" \
  -o test.md
```

3. Verify S3 file exists:
```bash
aws s3 ls s3://agent2-ingestor-bucket-us-east-1/documents/ --recursive | grep YOUR_DOC_ID
```

**Solutions**:
- Verify S3 files exist
- Check Lambda IAM role has `s3:GetObject` permission
- Allow downloads in browser settings
- Check API Gateway binary media types include correct formats

---

### Issue 7: Statistics Cards Show Zero

**Symptom**: Statistics cards all show 0 documents

**Possible Causes**:
1. Manifest is empty or doesn't exist
2. API endpoint failing
3. Frontend not calling API correctly

**Diagnostic Steps**:

1. Test stats endpoint:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev/documents/stats"
```

2. Check manifest has documents:
```bash
aws s3 cp s3://agent2-ingestor-bucket-us-east-1/manifest.json - | jq '.document_count'
```

3. Check browser console for API errors

**Solutions**:
- Upload and process documents
- Verify manifest.json exists and has documents
- Check API endpoint returns correct data
- Verify frontend is calling the right endpoint

---

### Issue 8: EventBridge Processing Not Working

**Symptom**: Jobs stuck in "queued" status forever

**Possible Causes**:
1. EventBridge rule disabled
2. Lambda doesn't have EventBridge invoke permission
3. Event not being sent to EventBridge
4. Lambda handler not processing EventBridge events

**Diagnostic Steps**:

1. Check EventBridge rule status:
```bash
aws events describe-rule \
  --name agent2-ingestor-document-processing-dev \
  --event-bus-name agent2-ingestor-events-dev \
  --region us-east-1 \
  --query 'State' --output text
```

2. Check recent EventBridge invocations:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name Invocations \
  --dimensions Name=RuleName,Value=agent2-ingestor-document-processing-dev \
  --start-time 2025-10-02T00:00:00Z \
  --end-time 2025-10-02T23:59:59Z \
  --period 3600 \
  --statistics Sum \
  --region us-east-1
```

3. Check Lambda logs for EventBridge events:
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/agent2-ingestor-api-dev \
  --filter-pattern "agent2.ingestor" \
  --region us-east-1
```

4. Test EventBridge manually:
```bash
cd infrastructure
./test-eventbridge.sh
```

**Solutions**:
- Enable EventBridge rule if disabled
- Verify Lambda has EventBridge permission in IAM role
- Check event_bus_name environment variable is set
- Verify Lambda handler routes EventBridge events correctly
- Check orchestration_service.py is sending events

---

## General Debugging Tips

### 1. Check Lambda Logs
```bash
# Tail logs in real-time
aws logs tail /aws/lambda/agent2-ingestor-api-dev --follow --region us-east-1

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/agent2-ingestor-api-dev \
  --filter-pattern "ERROR" \
  --region us-east-1
```

### 2. Test API Endpoints Directly

Get your auth token:
1. Open browser DevTools (F12)
2. Go to Application tab
3. Click Cookies
4. Find `idToken` value
5. Copy the token

Test endpoints:
```bash
TOKEN="your-token-here"
API_URL="https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev"

# Health check
curl $API_URL/health

# List documents
curl -H "Authorization: Bearer $TOKEN" "$API_URL/documents"

# Search
curl -H "Authorization: Bearer $TOKEN" "$API_URL/documents/search?q=test"

# Stats
curl -H "Authorization: Bearer $TOKEN" "$API_URL/documents/stats"
```

### 3. Check AWS Resources

```bash
# Lambda function exists and is updated
aws lambda get-function \
  --function-name agent2-ingestor-api-dev \
  --region us-east-1 \
  --query 'Configuration.[LastModified,Environment.Variables]'

# S3 bucket contents
aws s3 ls s3://agent2-ingestor-bucket-us-east-1/ --recursive --human-readable

# DynamoDB table
aws dynamodb describe-table \
  --table-name document-jobs \
  --region us-east-1 \
  --query 'Table.[TableStatus,ItemCount]'

# EventBridge event bus
aws events list-event-buses \
  --region us-east-1 \
  --query 'EventBuses[?Name==`agent2-ingestor-events-dev`]'
```

### 4. Browser DevTools

Always check:
- **Console tab**: JavaScript errors
- **Network tab**: Failed API requests (look for red)
- **Application tab**: Cookies and local storage
- **Performance tab**: Slow loading issues

### 5. Clear Caches

Sometimes old code is cached:
```bash
# Clear browser cache
# Chrome: Ctrl+Shift+Delete
# Safari: Cmd+Option+E

# Hard refresh
# Chrome: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
# Safari: Cmd+Option+R

# Clear CloudFront cache (if using)
aws cloudfront create-invalidation \
  --distribution-id YOUR_DIST_ID \
  --paths "/*"
```

---

## Quick Fixes Checklist

When things aren't working, try this checklist:

### Backend Issues
- [ ] Check Lambda function is deployed (check LastModified date)
- [ ] Verify environment variables set (EVENT_BUS_NAME, S3_BUCKET, etc.)
- [ ] Check CloudWatch logs for errors
- [ ] Verify IAM permissions (S3, DynamoDB, EventBridge)
- [ ] Test API endpoints with curl

### Frontend Issues
- [ ] Check browser console for errors
- [ ] Verify API_URL environment variable correct
- [ ] Hard refresh browser (Ctrl+Shift+R)
- [ ] Check Network tab for failed requests
- [ ] Verify auth token is valid (not expired)

### Data Issues
- [ ] Check manifest.json exists in S3
- [ ] Verify documents exist in S3
- [ ] Check DynamoDB jobs table has completed jobs
- [ ] Verify EventBridge rule is enabled

### Deployment Issues
- [ ] Check Amplify build succeeded
- [ ] Verify SAM deployment completed
- [ ] Check CloudFormation stack status
- [ ] Verify correct Git branch deployed

---

## Getting Help

If issues persist after trying troubleshooting steps:

1. **Collect diagnostic information**:
   - Browser console errors (screenshot)
   - Network tab failed requests
   - CloudWatch logs (last 50 lines)
   - API endpoint test results

2. **Check documentation**:
   - DOCUMENT_VIEWING_GUIDE.md
   - EVENTBRIDGE_ARCHITECTURE.md
   - ROUTE_ORDERING_FIX.md
   - ARCHITECTURE.md

3. **Verify versions**:
   ```bash
   # Frontend version
   cat frontend/src/version.json
   
   # Backend version (check git commit)
   git log -1 --oneline
   
   # Lambda last update
   aws lambda get-function \
     --function-name agent2-ingestor-api-dev \
     --query 'Configuration.LastModified' --output text
   ```

4. **Check recent changes**:
   ```bash
   git log --oneline -10
   ```

---

## Prevention Tips

To avoid common issues:

1. **Always test locally before deploying**
2. **Check route ordering when adding new endpoints**
3. **Verify environment variables after deployment**
4. **Monitor CloudWatch logs during testing**
5. **Test with different browsers**
6. **Clear cache after deployments**
7. **Use semantic versioning for frontend builds**
8. **Document any custom configuration**
9. **Keep documentation updated**
10. **Test error paths, not just happy paths**
