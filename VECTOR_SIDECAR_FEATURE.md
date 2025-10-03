# Vector Sidecar Data Feature Explanation

## What is the Vector Sidecar Data?

The **Vector Sidecar Data** is a comprehensive JSON file that contains AI-generated vector embeddings and metadata for each processed document. It's the "secret sauce" that enables semantic search and AI-powered document understanding.

---

## What Should This UX Feature Display?

### When Working Correctly

The Vector Sidecar Data accordion on the Document Viewer page should display:

1. **Expandable Accordion**
   - Title: "Vector Sidecar Data"
   - Icon: Storage icon (database symbol)
   - Expandable with down arrow

2. **When Expanded - Shows Formatted JSON** containing:

#### Top-Level Metadata
```json
{
  "source": "document.pdf",
  "created_at": "2025-10-03T10:30:45.123Z",
  "embedding_model": "amazon.titan-embed-text-v1",
  "embedding_dimensions": 1536,
  "total_chunks": 25,
  "successful_chunks": 25,
  "failed_chunks": 0
}
```

#### Chunking Strategy
```json
{
  "chunking_strategy": {
    "chunk_size": 1024,
    "overlap_size": 100,
    "dynamic_sizing": true,
    "preserve_boundaries": true
  }
}
```

#### Processing Statistics
```json
{
  "processing_statistics": {
    "original_word_count": 5000,
    "original_character_count": 32500,
    "estimated_total_tokens": 6500,
    "embedded_tokens": 6450,
    "average_chunk_size_words": 258.5,
    "total_embedding_time_seconds": 45.23,
    "average_embedding_time_per_chunk": 1.809
  }
}
```

#### Quality Metrics
```json
{
  "quality_metrics": {
    "success_rate": 100.0,
    "chunk_utilization": 99.85
  }
}
```

#### Chunks Array (The Big One!)
Each chunk contains:
```json
{
  "chunks": [
    {
      "chunk_id": "document.pdf_0000_a1b2c3d4e5f6g7h8",
      "chunk_index": 0,
      "text": "The actual text content of this chunk...",
      "embedding": [0.123, -0.456, 0.789, ... 1536 numbers total],
      "metadata": {
        "source": "document.pdf",
        "chunk_index": 0,
        "word_count": 256,
        "character_count": 1542,
        "estimated_tokens": 333,
        "chunk_hash": "a1b2c3d4e5f6g7h8",
        "embedding_timestamp": "2025-10-03T10:30:45.456Z",
        "embedding_generation_time_seconds": 1.823,
        "embedding_dimensions": 1536,
        "embedding_model_version": "amazon.titan-embed-text-v1"
      }
    },
    // ... repeated for each chunk (25 in this example)
  ]
}
```

---

## Purpose & Use Cases

### 1. **Transparency**
Shows users exactly how their document was processed by AI:
- How many chunks were created
- What chunking strategy was used
- Processing time and statistics
- Success rate

### 2. **Debugging**
Allows developers/power users to:
- Verify embeddings were generated
- Check chunk quality and size
- Identify failed chunks
- Review processing errors

### 3. **Quality Assurance**
Users can:
- See the success rate of embedding generation
- Review the actual text in each chunk
- Verify important content wasn't missed
- Check if chunking preserved meaning

### 4. **Technical Inspection**
Advanced users can:
- Examine the 1536-dimensional vector embeddings
- Review metadata for each chunk
- Understand token usage
- Analyze processing time

### 5. **Future AI Features**
This data enables:
- Semantic search (finding similar content)
- AI-powered Q&A about documents
- Document similarity comparison
- Context-aware retrieval

---

## Why Might It Not Be Showing?

### Possible Issues

#### 1. **Sidecar File Doesn't Exist**
The document may have been processed before the sidecar feature was implemented.

**Check**:
```bash
# Look at the manifest
aws s3 cp s3://agent2-ingestor-bucket-us-east-1/manifest.json - | jq '.documents[] | select(.document_id=="YOUR_DOC_ID")'

# Check if sidecar_s3_key is present and not null
```

**Solution**: Reprocess the document to generate sidecar data.

#### 2. **Backend Not Retrieving Sidecar**
The backend `get_document_by_id` method might be failing silently.

**Check Backend Logs**:
```bash
aws logs tail /aws/lambda/agent2-ingestor-api-dev --follow --region us-east-1 | grep -i sidecar
```

**Look for warnings**: "Warning: Could not load sidecar data"

#### 3. **S3 File Missing**
The sidecar file referenced in manifest doesn't exist in S3.

**Check**:
```bash
# Get sidecar key from manifest first, then:
aws s3 ls s3://agent2-ingestor-bucket-us-east-1/sidecars/
```

#### 4. **Frontend Not Receiving Data**
The API might return null for sidecar_data.

**Debug in Browser**:
1. Open DevTools (F12)
2. Go to Network tab
3. Click on a document to view
4. Find the API request to `/documents/{documentId}`
5. Check Response:
```json
{
  "document_id": "...",
  "sidecar_data": null  // ← Problem!
}
```

#### 5. **Accordion Only Shows If Data Exists**
The code only renders the accordion if `document.sidecar_data` is truthy:

```tsx
{document.sidecar_data && (
  <Accordion>
    // ... sidecar display
  </Accordion>
)}
```

If `sidecar_data` is null/undefined, the accordion won't appear at all.

---

## How to Diagnose the Issue

### Step 1: Check Browser Console
```javascript
// Open DevTools Console when viewing a document
// The component should log errors if any
```

### Step 2: Inspect API Response
```bash
# Get your auth token from browser cookies (idToken)
TOKEN="your-token-here"

# Call API directly
curl -H "Authorization: Bearer $TOKEN" \
  "https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev/documents/YOUR_DOC_ID" | jq '.sidecar_data'
```

**Expected**: Should return large JSON object with chunks array
**Problem**: Returns `null`

### Step 3: Check Manifest
```bash
aws s3 cp s3://agent2-ingestor-bucket-us-east-1/manifest.json - | \
  jq '.documents[] | select(.document_id=="YOUR_DOC_ID") | {sidecar_s3_key, chunk_count}'
```

**Expected**: 
```json
{
  "sidecar_s3_key": "sidecars/job123/20251003_document.sidecar.json",
  "chunk_count": 25
}
```

**Problem**: `sidecar_s3_key` is null or missing

### Step 4: Verify S3 File Exists
```bash
# Use the sidecar_s3_key from above
aws s3 ls s3://agent2-ingestor-bucket-us-east-1/sidecars/job123/20251003_document.sidecar.json
```

**Expected**: Shows file size and date
**Problem**: NoSuchKey error

### Step 5: Check Lambda Logs
```bash
aws logs tail /aws/lambda/agent2-ingestor-api-dev --follow --region us-east-1
```

Then view a document and look for:
- "Warning: Could not load sidecar data"
- Any S3 access errors
- JSON parsing errors

---

## Expected File Size

Sidecar files can be quite large:
- **Small document** (500 words): ~50-100 KB
- **Medium document** (2000 words): ~200-500 KB
- **Large document** (10,000 words): 1-5 MB

Most of the size comes from the embedding vectors (1536 numbers × 8 bytes each × number of chunks).

---

## How to Fix

### If Sidecar File Missing

**Option 1: Reprocess Document**
Upload the document again to trigger new processing with sidecar generation.

**Option 2: Manual Reprocessing** (if you have the original file)
```bash
# Trigger reprocessing via API (feature would need to be implemented)
# OR re-upload the file with same name
```

### If Backend Failing to Retrieve

1. Check Lambda has S3 read permissions
2. Verify the sidecar_s3_key in manifest is correct
3. Check CloudWatch logs for errors
4. Verify S3 bucket name is correct in environment variables

### If Data Too Large for Display

The sidecar JSON can be several MB. The accordion might:
- Take time to render
- Cause browser performance issues
- Need scrolling within the accordion

**Potential Improvement**: Implement pagination or summary view showing:
- Top-level metadata only by default
- "Load Full Data" button to fetch complete chunks array
- Or show first 10 chunks with "Load More" button

---

## Visual Example

When working correctly, users would see:

```
┌─────────────────────────────────────────────┐
│ Document Viewer: example.pdf                │
├─────────────────────────────────────────────┤
│                                             │
│ [Document metadata cards]                   │
│                                             │
│ ┌───────────────────────────────────────┐  │
│ │ 📄 Markdown Content                    │  │
│ │ ─────────────────────────────────────  │  │
│ │ # Document Title                       │  │
│ │ This is the rendered markdown...       │  │
│ └───────────────────────────────────────┘  │
│                                             │
│ ┌───────────────────────────────────────┐  │
│ │ 💾 Vector Sidecar Data          [▼]   │  │ ← Collapsed
│ └───────────────────────────────────────┘  │
│                                             │
└─────────────────────────────────────────────┘

After clicking to expand:

┌─────────────────────────────────────────────┐
│ 💾 Vector Sidecar Data          [▲]        │  ← Expanded
├─────────────────────────────────────────────┤
│ {                                           │
│   "source": "example.pdf",                  │
│   "created_at": "2025-10-03T...",          │
│   "embedding_model": "amazon.titan...",    │
│   "total_chunks": 25,                      │
│   "successful_chunks": 25,                 │
│   ...                                      │
│   "chunks": [                              │
│     {                                      │
│       "chunk_id": "example_0000...",      │
│       "text": "First chunk text...",      │
│       "embedding": [0.123, -0.456, ...],  │
│       ...                                  │
│     }                                      │
│   ]                                        │
│ }                                          │
│ [Scrollable if too long]                  │
└─────────────────────────────────────────────┘
```

---

## Recommendations

### Short-term Fixes

1. **Add Loading State**: Show "Loading sidecar data..." while fetching
2. **Better Error Handling**: Display specific error message if sidecar fails to load
3. **Check Icon**: Show checkmark if sidecar exists, warning icon if missing

### Medium-term Improvements

1. **Summary View**: Show key metrics without loading full chunks array
2. **Lazy Loading**: Only load chunks when accordion is expanded
3. **Pagination**: Show chunks in pages of 10 instead of all at once
4. **Search Within Chunks**: Add search box to find specific text in chunks

### Long-term Enhancements

1. **Visualization**: 
   - Chart showing chunk sizes
   - Timeline of processing
   - Heatmap of embedding dimensions

2. **Chunk Preview**: 
   - Table view of chunks with text snippets
   - Click to expand individual chunk details
   - Filter by chunk metadata

3. **Export Options**:
   - Download just the metadata (without embeddings)
   - Download specific chunks
   - Export as CSV for analysis

---

## Summary

**What it SHOULD do**: Display comprehensive JSON containing AI-generated vector embeddings, chunking strategy, processing statistics, and quality metrics for the document.

**Why it's not showing**: Most likely the sidecar file doesn't exist in S3, or the backend is failing to retrieve it. The accordion only renders if `document.sidecar_data` has a value.

**How to fix**: 
1. Check API response in browser DevTools Network tab
2. Verify sidecar_s3_key exists in manifest
3. Confirm S3 file exists at that key
4. Check Lambda logs for retrieval errors
5. Reprocess document if sidecar is missing

**Value to users**: Provides transparency into AI processing, enables debugging, supports future semantic search features, and allows quality assurance of document processing.
