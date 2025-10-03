# FastAPI Route Ordering Fix

## Issue

The Documents page was returning **HTTP 404** error when trying to access `/documents` endpoint.

## Root Cause

**FastAPI matches routes in order**. When routes are defined like this:

```python
@app.get("/documents")           # Less specific
@app.get("/documents/{document_id}")  # Catches everything including "search"
@app.get("/documents/search")    # Never reached!
```

The route `/documents/{document_id}` will match `/documents/search` because FastAPI sees "search" as a `document_id` parameter.

## Solution

**Define routes from MOST specific to LEAST specific**:

```python
# ✅ CORRECT ORDER - Most specific first
@app.get("/documents/search")           # Most specific (exact path)
@app.get("/documents/manifest")         # Specific (exact path)
@app.get("/documents/stats")            # Specific (exact path)
@app.get("/documents/{document_id}/download")  # Specific with param
@app.get("/documents/{document_id}")    # Path parameter (catches anything not matched above)
@app.get("/documents")                   # Base route (least specific)
```

## Rule of Thumb

When working with FastAPI routes:

1. **Static paths before dynamic paths**
   - `/documents/search` before `/documents/{id}`
   
2. **More specific before less specific**
   - `/documents/{id}/download` before `/documents/{id}`
   
3. **Longer paths before shorter paths**
   - `/documents/{id}/metadata` before `/documents/{id}`

## Testing

After reordering:
```bash
# These should all work now:
curl /documents                    # Lists documents
curl /documents/search?q=test      # Searches documents
curl /documents/stats              # Gets statistics
curl /documents/manifest           # Gets manifest
curl /documents/{id}               # Gets specific document
curl /documents/{id}/download      # Downloads document
```

## Files Modified

- `backend/main.py` - Reordered document endpoints (lines 1170-1303)

## Deployment

```bash
cd backend
sam build && sam deploy
```

## Verification

After deployment, test the endpoint:
```bash
TOKEN="your-jwt-token"
curl -H "Authorization: Bearer $TOKEN" \
  https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev/documents
```

Should return:
```json
{
  "documents": [...],
  "total": 0,
  "limit": 50,
  "offset": 0,
  "has_more": false
}
```

Not:
```json
{
  "detail": "Not Found"
}
```

## Lesson Learned

Always consider route ordering when adding new FastAPI endpoints, especially when mixing static paths with path parameters!
