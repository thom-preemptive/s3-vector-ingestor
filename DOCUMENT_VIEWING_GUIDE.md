# Document Viewing and Search Features

## Overview

The agent2_ingestor now includes comprehensive document viewing and search capabilities, allowing users to browse, search, and view all processed documents with their markdown content and vector sidecar data.

## Features

### 1. Documents Page (`/documents`)

**Location**: Main navigation → Documents

**Capabilities**:
- **List all documents** with pagination (20 per page)
- **Search documents** by filename, job name, or user ID
- **View statistics**: Total documents, PDF/URL counts, total size
- **Quick actions**: View document, download markdown

**Statistics Cards**:
- Total Documents
- PDF Documents  
- URL Documents
- Total Storage Size

**Search**:
- Real-time search as you type
- Searches across:
  - Filenames
  - Job names
  - User IDs
- Highlights which field matched

### 2. Document Viewer Page (`/documents/:documentId`)

**Location**: Click "View" icon on any document in Documents page

**Capabilities**:
- **View full markdown content** - Rendered with proper formatting
- **View sidecar/vector data** - JSON format in expandable accordion
- **Download options**:
  - Download as Markdown (.md)
  - Download as JSON (includes all metadata + sidecar)
- **Document metadata**:
  - Filename, job name, source type
  - File size, processing date
  - Document ID, Job ID
  - S3 storage keys

**Markdown Rendering**:
- Headings (H1, H2, H3)
- Paragraphs
- Code blocks (inline and block)
- Lists (ordered and unordered)
- Proper syntax highlighting

### 3. Backend API Endpoints

#### `GET /documents`
List documents with pagination
```
Query Parameters:
- limit (default: 50, max: 100)
- offset (default: 0)

Response:
{
  "documents": [...],
  "total": 150,
  "limit": 50,
  "offset": 0,
  "has_more": true
}
```

#### `GET /documents/{document_id}`
Get complete document with content
```
Response:
{
  "document_id": "...",
  "filename": "...",
  "markdown_content": "# Document Content...",
  "sidecar_data": { ... },
  ...
}
```

#### `GET /documents/search?q={query}`
Search documents
```
Query Parameters:
- q: Search query (min 2 characters)
- limit (default: 50)

Response:
{
  "query": "hazard",
  "results": [
    {
      ...document,
      "match_field": "filename"
    }
  ],
  "count": 3
}
```

#### `GET /documents/stats`
Get document statistics
```
Response:
{
  "total_documents": 150,
  "pdf_documents": 120,
  "url_documents": 30,
  "total_size_bytes": 52428800,
  "latest_upload": "2025-10-02T21:00:00Z",
  "unique_users": 5,
  "unique_jobs": 45
}
```

#### `GET /documents/{document_id}/download?format={format}`
Download document
```
Query Parameters:
- format: "markdown" or "json"

Response:
- markdown: text/markdown file
- json: application/json file
```

#### `GET /documents/manifest`
Get complete manifest with all documents
```
Response:
{
  "version": "1.0",
  "created_at": "...",
  "updated_at": "...",
  "document_count": 150,
  "documents": [...]
}
```

## Usage Examples

### Browsing Documents
1. Navigate to **Documents** from main menu
2. View statistics cards showing document counts
3. Scroll through paginated list
4. Use pagination controls at bottom

### Searching for Documents
1. Type search query in search bar (min 2 characters)
2. Press Enter or click "Search"
3. Results show matching documents with highlighted match field
4. Click "Clear" to return to full list

### Viewing a Document
1. Click the eye icon (👁️) on any document
2. View metadata in two panels:
   - **Document Information**: Job name, source type, size, date
   - **Storage Details**: IDs and S3 keys
3. Scroll down to see:
   - **Markdown Content**: Fully rendered document
   - **Vector Sidecar Data**: Expandable JSON view

### Downloading Documents
**From Documents Page**:
- Click download icon (⬇️) to download as markdown

**From Document Viewer**:
- Click markdown icon to download as .md
- Click JSON icon to download as .json with full metadata

## Technical Implementation

### Frontend Components

**DocumentsPage.tsx**:
- Material-UI table with pagination
- Real-time search with debouncing
- Statistics cards using Grid layout
- Icons for different source types (PDF, URL)

**DocumentViewerPage.tsx**:
- React Markdown for content rendering
- Expandable accordion for sidecar data
- Material-UI cards for metadata
- Custom download handlers

### Frontend Services

**api.ts** additions:
```typescript
- listDocuments(limit, offset)
- getDocument(documentId)
- searchDocuments(query, limit)
- getDocumentStats()
- downloadDocument(documentId, format)
```

### Backend Services

**aws_services.py** additions:
```python
- get_document_content(s3_key)
- get_sidecar_data(s3_key)
- get_document_by_id(document_id)
- list_documents(limit, offset)
- search_documents(query, limit)
```

### Routing

**App.tsx** routes:
```tsx
<Route path="/documents" element={<DocumentsPage />} />
<Route path="/documents/:documentId" element={<DocumentViewerPage />} />
```

**Layout.tsx** navigation:
```tsx
{ text: 'Documents', icon: <DescriptionIcon />, path: '/documents' }
```

## Dependencies

**New npm packages**:
- `react-markdown` - Markdown rendering with proper formatting

## Security

- All endpoints require **JWT authentication**
- User sessions validated via AWS Cognito
- S3 access controlled via IAM policies
- Document access logs tracked in CloudWatch

## Performance

- **Pagination**: Documents page shows 20 per page
- **Search**: Client-side debouncing prevents excessive API calls
- **Caching**: Browser caches document content
- **Lazy loading**: Sidecar data loaded on demand (accordion)

## Future Enhancements

Potential improvements:
1. **Full-text search** - Search within document content
2. **Filters** - Filter by date range, source type, user
3. **Sorting** - Sort by size, date, name
4. **Bulk actions** - Download multiple documents
5. **Document preview** - Preview before opening full view
6. **Sharing** - Generate shareable links
7. **Annotations** - Add notes/comments to documents
8. **Version history** - Track document revisions

## Troubleshooting

### No documents showing
- Check if any jobs have completed successfully
- Verify manifest.json exists in S3 bucket
- Check CloudWatch logs for API errors

### Search not working
- Ensure query is at least 2 characters
- Check browser console for errors
- Verify API endpoint is accessible

### Download fails
- Check S3 permissions for document keys
- Verify document exists in S3
- Check browser's download settings

### Markdown not rendering
- Verify react-markdown is installed: `npm list react-markdown`
- Check for markdown syntax errors in content
- Review browser console for rendering errors

## Deployment

### Backend
```bash
cd backend
sam build && sam deploy
```

### Frontend
```bash
cd frontend
npm install  # Install react-markdown
npm run build
# Deploy to Amplify (automatic via Git push)
```

## API Testing

### Test document listing
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev/documents
```

### Test document search
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev/documents/search?q=hazard"
```

### Test document retrieval
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev/documents/{document_id}
```

### Test statistics
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev/documents/stats
```

## Files Modified/Created

### Backend
- `backend/services/aws_services.py` - Added document retrieval methods
- `backend/main.py` - Added 6 new API endpoints

### Frontend
- `frontend/src/components/DocumentsPage.tsx` - **NEW** - Browse/search page
- `frontend/src/components/DocumentViewerPage.tsx` - **NEW** - Document viewer
- `frontend/src/services/api.ts` - Added 5 new API methods
- `frontend/src/App.tsx` - Added 2 new routes
- `frontend/src/components/Layout.tsx` - Added Documents menu item
- `frontend/package.json` - Added react-markdown dependency

### Documentation
- `DOCUMENT_VIEWING_GUIDE.md` - **THIS FILE**
