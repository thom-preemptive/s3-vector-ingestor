# 413 Content Too Large - S3 Presigned URL Solution

## The Problem

Browser console showed:
```
POST https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev/upload/pdf 
net::ERR_FAILED 413 (Content Too Large)
```

**Root Cause**: API Gateway REST API has a hard **10MB payload limit**. PDFs larger than 10MB cannot be uploaded directly through the API.

## The Solution: S3 Presigned URLs

Instead of uploading through API Gateway, we now upload directly to S3:

### Architecture

**Before** (Failed for files > 10MB):
```
Browser → API Gateway → Lambda → S3
         (10MB limit!)
```

**After** (Works for any file size):
```
Browser → API Gateway → Lambda (get presigned URL)
Browser → S3 directly (no size limit!)
Browser → API Gateway → Lambda (process file from S3)
```

### Three-Step Upload Process

#### Step 1: Get Presigned URL
```
POST /upload/presigned-url
Headers: Authorization: Bearer <token>
Body: filename, content_type
Response: { upload_url, file_key }
```

#### Step 2: Upload to S3
```
PUT <upload_url>
Headers: Content-Type: application/pdf
Body: <file binary data>
```

#### Step 3: Trigger Processing
```
POST /upload/process-s3-files
Headers: Authorization: Bearer <token>
Body: {
  files: [{ file_key, filename }],
  job_name,
  approval_required
}
Response: { job_id, status }
```

## Backend Changes

### New Endpoints

**`POST /upload/presigned-url`**
- Generates S3 presigned URL for direct upload
- Valid for 15 minutes
- Returns upload URL and file key

**`POST /upload/process-s3-files`**
- Processes files already uploaded to S3
- Downloads from S3 and runs document processing
- Creates job and returns job_id

### Configuration Updates

**template.yaml**:
```yaml
Lambda:
  Timeout: 900  # 15 minutes (was 30 seconds)
  MemorySize: 3008  # Increased for large files

API Gateway:
  BinaryMediaTypes:
    - multipart/form-data
    - application/pdf
    - application/octet-stream
```

## Frontend Changes

### Updated uploadDocument()

The `apiService.uploadDocument()` function now:

1. Extracts files from FormData
2. For each file:
   - Gets presigned URL from backend
   - Uploads file directly to S3 using PUT
   - Collects S3 file keys
3. Calls backend to process all uploaded files
4. Returns job_id

### Benefits

✅ **No size limit**: Files can be gigabytes
✅ **Faster uploads**: Direct to S3, no Lambda processing
✅ **Better reliability**: S3 handles multipart uploads
✅ **Cost effective**: No Lambda execution time during upload
✅ **Secure**: Presigned URLs expire after 15 minutes

## Testing

Once Amplify deploys version 0.55:

1. **Try uploading a large PDF** (>10MB)
2. **Check console logs**:
   ```
   uploadDocument: Starting upload process
   uploadDocument: Token retrieved: Yes
   uploadDocument: Uploading N files via S3 presigned URLs
   uploadDocument: Got presigned URL for file.pdf
   uploadDocument: Successfully uploaded file.pdf to S3
   uploadDocument: Triggering backend processing
   uploadDocument: Process response status: 200
   uploadDocument: Success! Result: { job_id: "uuid..." }
   ```
3. **Verify real job ID** (not "mock-")
4. **Check Jobs page** for the uploaded job

## Security

- ✅ Presigned URLs require authentication to obtain
- ✅ URLs expire after 15 minutes
- ✅ Files uploaded to user-specific S3 paths
- ✅ Backend validates user before processing

## Deployment

- ✅ Backend deployed with new endpoints and Lambda config
- ✅ Frontend version 0.55 pushed to Amplify
- ⏳ Amplify building (check console for completion)

---

**This should finally fix the upload issue!** 🎉
