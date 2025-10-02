# DIAGNOSTIC APPROACH - v0.54

## The Problem
After multiple attempts to fix the authentication issue, uploads still return "mock-" job IDs and the jobs page is blank, indicating API calls are failing silently.

## New Approach: Diagnosis BEFORE Fixes

Instead of making more blind code changes, I've created a **Diagnostic Page** that will tell us EXACTLY what's wrong.

## How to Use the Diagnostic Page

1. **Wait for Amplify Deployment** (~2-3 minutes)
   - Check your Amplify console for build completion
   - Version should show 0.54

2. **Navigate to the Diagnostic Page**
   - After logging in, click **"Diagnostics"** in the left sidebar
   - Or go directly to: `https://your-app.amplifyapp.com/diagnostics`

3. **Click "Run Diagnostics"**
   - This will run 6 comprehensive tests
   - Each test will show ✓ Success, ⚠ Info, or ✗ Error
   - Detailed JSON output will be shown for each test

## What the Diagnostic Tests Check

### Test 1: Amplify Configuration
- Verifies Amplify is configured with Auth and API settings
- **What we're looking for**: Cognito config present

### Test 2: Environment Variables
- Checks if `REACT_APP_API_URL`, `REACT_APP_COGNITO_USER_POOL_ID`, `REACT_APP_COGNITO_CLIENT_ID` are set
- **What we're looking for**: All three should be present
- **If missing**: Amplify environment variables not configured properly

### Test 3: Auth Session
- Attempts to retrieve JWT token using `fetchAuthSession()`
- **What we're looking for**: Token with length 800+ characters
- **If fails**: User not authenticated, or Amplify auth not working

### Test 4: Backend Health Check (Unauthenticated)
- Tests if backend API is reachable
- Makes request to `/health` endpoint (no auth required)
- **What we're looking for**: Status 200, `{"status":"healthy"}`
- **If fails**: Backend is down, wrong URL, or network issue

### Test 5: Authenticated API Call
- Tests the `/jobs` endpoint with authentication
- Sends the JWT token in Authorization header
- **What we're looking for**: Status 200, jobs array returned
- **If 401**: Token rejected by backend (Cognito mismatch)
- **If 403**: CORS or permissions issue
- **If network error**: CORS blocking the request

### Test 6: CORS Preflight
- Tests if CORS headers are properly configured
- **What we're looking for**: Access-Control-Allow-Origin: *

## Interpreting Results

### Scenario 1: Test 3 Fails (No Token)
**Problem**: Authentication not working in frontend
**Possible Causes**:
- User session expired
- Amplify configuration incorrect
- Cognito User Pool ID mismatch

**Next Steps**: Check Amplify environment variables match Cognito settings

### Scenario 2: Test 4 Fails (Backend Unreachable)
**Problem**: Cannot reach backend at all
**Possible Causes**:
- Wrong API URL in environment variables
- Backend Lambda not deployed
- API Gateway not configured

**Next Steps**: Verify `REACT_APP_API_URL` is correct, check backend deployment

### Scenario 3: Test 5 Fails with 401
**Problem**: Backend rejects the token
**Possible Causes**:
- Backend `COGNITO_USER_POOL_ID` doesn't match frontend
- Backend `COGNITO_CLIENT_ID` doesn't match frontend
- Token format incorrect

**Next Steps**: Verify backend environment variables in Lambda

### Scenario 4: Test 5 Fails with CORS Error
**Problem**: Browser blocking the request
**Possible Causes**:
- API Gateway CORS not configured
- Missing CORS headers in Lambda response

**Next Steps**: Check API Gateway CORS configuration

### Scenario 5: All Tests Pass
**Problem**: Diagnostic passes but upload still fails
**Possible Causes**:
- Different issue with `/upload/pdf` endpoint specifically
- FormData handling issue

**Next Steps**: Check Lambda logs for actual error

## After Running Diagnostics

**Share the full diagnostic output with me**, including:
- Which tests passed/failed
- The status codes returned
- The detailed JSON for any failed tests
- Any error messages

This will tell us EXACTLY what to fix instead of guessing.

## Quick Reference: Expected Values

```
REACT_APP_API_URL: https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev
REACT_APP_COGNITO_USER_POOL_ID: us-east-1_Yk8Yt64uE
REACT_APP_COGNITO_CLIENT_ID: 6hcundvt29da9ap8ji973h1pqq
```

Backend Lambda should have matching:
```
COGNITO_USER_POOL_ID: us-east-1_Yk8Yt64uE
COGNITO_CLIENT_ID: 6hcundvt29da9ap8ji973h1pqq
```

## No More Guessing
This diagnostic page will end the back-and-forth. We'll know exactly what's broken and fix it once.
