# Debugging Authentication Issues

## Version 0.52 - Enhanced Logging

The latest deployment includes detailed console logging to help diagnose why API calls are returning mock data.

## How to Debug

### 1. Open Browser Console
- **Chrome/Edge**: Press F12 or Cmd+Option+I (Mac)
- **Firefox**: Press F12 or Cmd+Option+K (Mac)
- Go to the **Console** tab

### 2. Try Uploading a Document

Look for these log messages in order:

```
uploadDocument: Starting upload to https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev/upload/pdf
Auth session: {tokens: {...}, ...}
ID Token retrieved: Yes (length: XXX)
uploadDocument: Token retrieved: Yes (length: XXX)
uploadDocument: Response status: 200
uploadDocument: Success! Result: {...}
```

### 3. Common Issues and What to Look For

#### Issue: "ID Token retrieved: No"
**Problem**: AWS Amplify is not providing a JWT token
**Possible Causes**:
- User is not fully authenticated
- Token has expired
- Amplify configuration issue

**Solution**: Try logging out and logging back in

#### Issue: "uploadDocument: Response status: 401"
**Problem**: Backend rejected the token
**Possible Causes**:
- Token format incorrect
- Token expired
- Backend Cognito configuration mismatch

**What to check**:
- Look at the error response body in the console
- Verify Cognito User Pool ID and Client ID match between frontend and backend

#### Issue: "uploadDocument: Response status: 403"
**Problem**: CORS or permissions issue
**Possible Causes**:
- API Gateway CORS misconfiguration
- Missing IAM permissions

#### Issue: "uploadDocument: Caught error: TypeError: Failed to fetch"
**Problem**: Network or CORS issue
**Possible Causes**:
- Backend is down
- CORS headers not set correctly
- Wrong API endpoint URL

**What to check**:
- Verify backend is deployed: https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev/health
- Check Network tab for the actual error

### 4. Check Backend Health

Open this URL in a browser:
```
https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev/health
```

You should see:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-01T..."
}
```

### 5. Testing Jobs Page

When viewing the Jobs page, look for:
```
getJobs: Fetching from https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev/jobs
Auth session: {tokens: {...}, ...}
ID Token retrieved: Yes (length: XXX)
getJobs: Response status: 200
getJobs: Success! Jobs count: X
```

If the jobs page is blank but you see "Success! Jobs count: 0", it means:
- Authentication is working ✓
- No jobs exist in the database yet
- Try uploading a document first

## Expected Flow

### Successful Upload:
1. User clicks Upload
2. `fetchAuthSession()` retrieves JWT from Amplify
3. Token is added to Authorization header
4. Backend verifies token with Cognito
5. Document is processed
6. Real job_id is returned (UUID format, not "mock-")

### Failed Upload (current issue):
1. User clicks Upload
2. Token retrieval fails OR backend rejects token
3. Catch block is triggered
4. Mock data is returned with job_id: "mock-1234567890"

## Next Steps Based on Console Output

Share the console output with me, especially:
- The full error message if any
- The Response status code
- Whether the token was retrieved
- The Network tab details for the failed request

This will help identify the exact issue!
