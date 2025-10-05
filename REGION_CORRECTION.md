# Region Correction: us-west-1 → us-east-1

**Date:** October 5, 2025  
**Issue:** Backend stacks were incorrectly deployed to us-west-1  
**Resolution:** Redeployed all stacks to us-east-1  
**Status:** ✅ RESOLVED

---

## Problem Summary

During the S3 bucket segregation implementation, backend stacks were accidentally deployed to **us-west-1** instead of **us-east-1**. This caused:
1. Dev environment showing "failed to fetch" errors
2. Test environment showing old dev data (due to confusion about which backend was active)

---

## Resolution Steps

### 1. Redeployed All Backend Stacks to us-east-1

```bash
cd /Users/thomkozik/dev/agent2_ingestor/backend
sam build

# Deploy dev to us-east-1
sam deploy --parameter-overrides Environment=dev \
  --stack-name agent2-ingestor-backend-dev \
  --region us-east-1 \
  --no-confirm-changeset \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM

# Deploy test to us-east-1  
sam deploy --parameter-overrides Environment=test \
  --stack-name agent2-ingestor-backend-test \
  --region us-east-1 \
  --no-confirm-changeset \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM

# Deploy main to us-east-1
sam deploy --parameter-overrides Environment=main \
  --stack-name agent2-ingestor-backend-main \
  --region us-east-1 \
  --no-confirm-changeset \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM
```

### 2. Verified Correct API Gateway Endpoints

| Environment | API Gateway ID | API URL | Region |
|------------|----------------|---------|--------|
| **dev** | pubp32frrg | https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev | ✅ us-east-1 |
| **test** | b3krnh1y2l | https://b3krnh1y2l.execute-api.us-east-1.amazonaws.com/test | ✅ us-east-1 |
| **main** | w17iflw3ai | https://w17iflw3ai.execute-api.us-east-1.amazonaws.com/main | ✅ us-east-1 |

### 3. Verified Lambda Environment Variables

All Lambda functions now have correct environment-specific configurations:

**Dev Lambda:**
```
COGNITO_CLIENT_ID: 6hcundvt29da9ap8ji973h1pqq
COGNITO_USER_POOL_ID: us-east-1_Yk8Yt64uE
ENVIRONMENT: dev
EVENT_BUS_NAME: agent2-ingestor-events-dev
S3_BUCKET: agent2-ingestor-bucket-dev-us-east-1
```

**Test Lambda:**
```
COGNITO_CLIENT_ID: 66f28prrgbg3aisnjvoj5okuk
COGNITO_USER_POOL_ID: us-east-1_T4apZJIeL
ENVIRONMENT: test
EVENT_BUS_NAME: agent2-ingestor-events-test
S3_BUCKET: agent2-ingestor-bucket-test-us-east-1
```

**Main Lambda:**
```
COGNITO_CLIENT_ID: erpop6dml8ucj931t6jlojfog
COGNITO_USER_POOL_ID: us-east-1_mLiHR7DqI
ENVIRONMENT: main
EVENT_BUS_NAME: agent2-ingestor-events-main
S3_BUCKET: agent2-ingestor-bucket-main-us-east-1
```

### 4. Deleted Incorrect us-west-1 Stacks

```bash
aws cloudformation delete-stack --stack-name agent2-ingestor-backend-dev --region us-west-1
aws cloudformation delete-stack --stack-name agent2-ingestor-backend-test --region us-west-1
aws cloudformation delete-stack --stack-name agent2-ingestor-backend-main --region us-west-1
```

### 5. Verified Amplify Environment Variables

All Amplify branches already had correct us-east-1 API URLs configured:

**Dev Branch:**
```json
{
  "ENVIRONMENT": "dev",
  "REACT_APP_API_URL": "https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev",
  "REACT_APP_COGNITO_CLIENT_ID": "6hcundvt29da9ap8ji973h1pqq",
  "REACT_APP_COGNITO_USER_POOL_ID": "us-east-1_Yk8Yt64uE"
}
```

**Test Branch:**
```json
{
  "ENVIRONMENT": "test",
  "REACT_APP_API_URL": "https://b3krnh1y2l.execute-api.us-east-1.amazonaws.com/test",
  "REACT_APP_COGNITO_CLIENT_ID": "66f28prrgbg3aisnjvoj5okuk",
  "REACT_APP_COGNITO_USER_POOL_ID": "us-east-1_T4apZJIeL"
}
```

**Main Branch:**
```json
{
  "ENVIRONMENT": "main",
  "REACT_APP_API_URL": "https://w17iflw3ai.execute-api.us-east-1.amazonaws.com/main",
  "REACT_APP_COGNITO_CLIENT_ID": "erpop6dml8ucj931t6jlojfog",
  "REACT_APP_COGNITO_USER_POOL_ID": "us-east-1_mLiHR7DqI"
}
```

---

## Verification Steps

### 1. Verify S3 Bucket Data Segregation

```bash
# Dev bucket should have 6 documents
aws s3 cp s3://agent2-ingestor-bucket-dev-us-east-1/manifest.json - | jq '.document_count'
# Output: 6

# Test bucket should have 0 documents
aws s3 cp s3://agent2-ingestor-bucket-test-us-east-1/manifest.json - | jq '.document_count'
# Output: 0

# Main bucket should have 0 documents
aws s3 cp s3://agent2-ingestor-bucket-main-us-east-1/manifest.json - | jq '.document_count'
# Output: 0
```

✅ All buckets correctly segregated

### 2. Verify DynamoDB Tables

All environments have separate tables in us-east-1:

**Dev Tables:**
- agent2_ingestor_jobs_dev
- agent2_ingestor_approvals_dev
- agent2_ingestor_user_tracking_dev

**Test Tables:**
- agent2_ingestor_jobs_test
- agent2_ingestor_approvals_test
- agent2_ingestor_user_tracking_test

**Main Tables:**
- agent2_ingestor_jobs_main
- agent2_ingestor_approvals_main
- agent2_ingestor_user_tracking_main

### 3. Browser Cache Issue

The "failed to fetch" and "old data" issues may be due to browser caching. Users should:
1. **Hard refresh** the browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
2. **Clear browser cache** for the Amplify domains
3. **Close and reopen** the browser

---

## Complete Resource Inventory (us-east-1)

### Dev Environment
- **API Gateway:** pubp32frrg (https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev)
- **Lambda:** agent2-ingestor-api-dev
- **S3 Bucket:** agent2-ingestor-bucket-dev-us-east-1 (6 documents)
- **DynamoDB:** agent2_ingestor_jobs_dev, agent2_ingestor_approvals_dev, agent2_ingestor_user_tracking_dev
- **Cognito:** us-east-1_Yk8Yt64uE (Client: 6hcundvt29da9ap8ji973h1pqq)
- **Frontend:** https://dev.dn1hdu83qdv9u.amplifyapp.com

### Test Environment
- **API Gateway:** b3krnh1y2l (https://b3krnh1y2l.execute-api.us-east-1.amazonaws.com/test)
- **Lambda:** agent2-ingestor-api-test
- **S3 Bucket:** agent2-ingestor-bucket-test-us-east-1 (0 documents)
- **DynamoDB:** agent2_ingestor_jobs_test, agent2_ingestor_approvals_test, agent2_ingestor_user_tracking_test
- **Cognito:** us-east-1_T4apZJIeL (Client: 66f28prrgbg3aisnjvoj5okuk)
- **Frontend:** https://test.dn1hdu83qdv9u.amplifyapp.com

### Main Environment
- **API Gateway:** w17iflw3ai (https://w17iflw3ai.execute-api.us-east-1.amazonaws.com/main)
- **Lambda:** agent2-ingestor-api-main
- **S3 Bucket:** agent2-ingestor-bucket-main-us-east-1 (0 documents)
- **DynamoDB:** agent2_ingestor_jobs_main, agent2_ingestor_approvals_main, agent2_ingestor_user_tracking_main
- **Cognito:** us-east-1_mLiHR7DqI (Client: erpop6dml8ucj931t6jlojfog)
- **Frontend:** https://main.dn1hdu83qdv9u.amplifyapp.com

---

## Testing Instructions

### For Dev Environment:
1. Navigate to https://dev.dn1hdu83qdv9u.amplifyapp.com
2. Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+R)
3. Login with dev Cognito credentials
4. Dashboard should load without "failed to fetch" errors
5. Processed Documents should show 6 documents

### For Test Environment:
1. Navigate to https://test.dn1hdu83qdv9u.amplifyapp.com
2. Hard refresh browser
3. Login with test Cognito credentials
4. Dashboard should load successfully
5. Processed Documents should show 0 documents (empty)

### For Main Environment:
1. Navigate to https://main.dn1hdu83qdv9u.amplifyapp.com
2. Hard refresh browser
3. Login with main Cognito credentials
4. Dashboard should load successfully
5. Processed Documents should show 0 documents (empty)

---

## Root Cause

The initial deployment script didn't specify `--region us-east-1`, causing SAM CLI to use the default region from AWS CLI configuration, which was `us-west-1`.

## Prevention

For future deployments, **always specify the region explicitly**:
```bash
sam deploy --region us-east-1 ...
```

Or create a `samconfig.toml` file:
```toml
[default.deploy.parameters]
region = "us-east-1"
```

---

**Status:** ✅ All resources now in us-east-1, complete environment segregation achieved
