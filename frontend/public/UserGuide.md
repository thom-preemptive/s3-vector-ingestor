Welcome to S3 Vector Store Ingestor, a cloud-ready document processing platform that converts PDFs and web content into AI-ready markdown and vector embeddings.

## Overview

S3 Vector Store Ingestor is designed to process emergency response documents, research materials, and other critical content by:

- **Extracting text** from PDFs using OCR (AWS Textract)
- **Converting web pages** to clean markdown format
- **Generating vector embeddings** for AI/ML applications
- **Providing real-time monitoring** of processing jobs
- **Enabling document search and viewing** across your processed content

## Main Features

### 🏠 Dashboard
**Purpose**: System overview and real-time monitoring
**Why it's needed**: Provides immediate visibility into system health, job processing status, and resource utilization

**Key Features**:
- **System Health**: Real-time status of all AWS services
- **Job Statistics**: Active jobs, completed jobs, failed jobs
- **Queue Status**: Processing queue depth and worker status
- **Storage Metrics**: S3 usage and DynamoDB performance
- **Recent Activity**: Latest job completions and system events

**How to use**:
1. Check system health indicators (green = healthy)
2. Monitor job completion rates
3. Review queue depths to understand processing load
4. Use for troubleshooting when issues arise

### 📤 Upload Documents
**Purpose**: Process PDF documents for text extraction and vectorization
**Why it's needed**: Converts static PDF files into searchable, AI-ready content

**Key Features**:
- **Drag & Drop Interface**: Easy file upload with visual feedback
- **Large File Support**: Handles PDFs up to 15MB with async processing
- **Progress Tracking**: Real-time upload and processing status
- **Notes Field**: Add contextual notes (stored separately from content)
- **Batch Processing**: Queue multiple documents for processing

**Supported Formats**:
- PDF documents (with OCR for scanned content)
- Automatic text extraction and cleaning
- Table and form recognition via AWS Textract

**How to use**:
1. Navigate to "Upload Documents"
2. Drag PDF files or click to browse
3. Add optional notes for context
4. Click "Upload" to start processing
5. Monitor progress in the Job Queue page

### 🌐 URL Scraping
**Purpose**: Convert web pages and online content into markdown format
**Why it's needed**: Captures dynamic web content for archival and analysis

**Key Features**:
- **URL Input**: Process single URLs or multiple URLs
- **Content Extraction**: Clean markdown conversion
- **Metadata Preservation**: Captures title, author, date
- **Notes Field**: Add contextual notes (stored separately from content)
- **Link Following**: Optional recursive link processing

**Supported Content**:
- HTML web pages
- Blog posts and articles
- Documentation sites
- Research papers (when available online)

**How to use**:
1. Navigate to "URL Scraping"
2. Enter one or more URLs
3. Add optional notes for context
4. Click "Process URLs"
5. Monitor progress in the Job Queue page

### 📋 Job Queue
**Purpose**: Monitor document processing jobs in real-time
**Why it's needed**: Provides transparency into processing pipeline and handles failures

**Key Features**:
- **Real-time Status**: Live updates of job progress
- **Job Details**: Processing stage, timestamps, error messages
- **Retry Failed Jobs**: Automatic and manual retry options
- **Job History**: Complete audit trail of all processing
- **Performance Metrics**: Processing times and success rates

**Job States**:
- **Queued**: Job submitted, waiting for processing
- **Processing**: Currently being worked on by Lambda workers
- **Completed**: Successfully processed and stored
- **Failed**: Processing error occurred

**How to use**:
1. Navigate to "Job Queue" to see all your jobs
2. Click on job rows for detailed information
3. Use filters to find specific jobs
4. Monitor for failed jobs that need attention

### 📚 Documents
**Purpose**: Browse, search, and view all processed documents
**Why it's needed**: Provides access to processed content and enables content discovery

**Key Features**:
- **Document Browser**: Paginated list of all documents
- **Full-text Search**: Search across filenames, job names, and user IDs
- **Statistics Overview**: Document counts, storage usage, source types
- **Document Viewer**: Full markdown rendering with sidecar data
- **Download Options**: Export as markdown or JSON with metadata

**Document Types**:
- **PDF Documents**: OCR-processed text content
- **URL Documents**: Web-scraped markdown content
- **Vector Sidecars**: AI-ready embeddings in JSON format

**How to use**:
1. Navigate to "Documents" for overview
2. Use search bar to find specific documents
3. Click "View" icon to open document viewer
4. Expand sidecar data to see vector embeddings
5. Download content for external use

### ✅ Approvals
**Purpose**: Workflow approval system for sensitive content
**Why it's needed**: Ensures quality control and compliance for regulated documents

**Key Features**:
- **Pending Approvals**: Review queue for new documents
- **Approval Workflow**: Approve or reject processed content
- **Audit Trail**: Complete history of approval decisions
- **User Permissions**: Role-based approval authority
- **Bulk Actions**: Process multiple approvals efficiently

**Approval States**:
- **Pending**: Awaiting review
- **Approved**: Cleared for use
- **Rejected**: Not approved with reason

**How to use**:
1. Check for pending approvals in dashboard
2. Review document content and metadata
3. Approve or reject based on quality/compliance
4. Add comments for rejection reasons

### ⚙️ Settings
**Purpose**: User preferences and system configuration
**Why it's needed**: Personalizes experience and controls system behavior

**Key Features**:
- **Profile Settings**: User information and preferences
- **Notification Settings**: Email and system alerts
- **API Keys**: Manage authentication tokens
- **Display Preferences**: Theme, language, layout options
- **Security Settings**: Password, MFA, session management

**How to use**:
1. Navigate to "Settings"
2. Update personal information
3. Configure notification preferences
4. Manage security settings

### 🔧 Diagnostics
**Purpose**: System troubleshooting and health monitoring
**Why it's needed**: Enables quick identification and resolution of issues

**Key Features**:
- **System Tests**: Automated health checks
- **Service Status**: Individual AWS service monitoring
- **Log Viewer**: Recent system and error logs
- **Performance Metrics**: Response times and throughput
- **Connectivity Tests**: Network and API endpoint validation

**Diagnostic Tools**:
- **API Connectivity**: Test backend service availability
- **Database Connections**: Verify DynamoDB and S3 access
- **Queue Health**: Check SQS queue status
- **Authentication**: Validate Cognito integration

**How to use**:
1. Navigate to "Diagnostics"
2. Run automated system tests
3. Review service status indicators
4. Check logs for error details
5. Use results to troubleshoot issues

## Technical Architecture

### Processing Pipeline
1. **Input**: PDF files or URLs submitted via web interface
2. **Authentication**: AWS Cognito validates user identity
3. **Job Creation**: FastAPI creates tracking record in DynamoDB
4. **Queue Processing**: Job queued in SQS with priority
5. **Worker Processing**: Lambda functions process documents
6. **Content Extraction**: Textract OCR for PDFs, scraping for URLs
7. **Text Processing**: Cleaning, formatting, markdown conversion
8. **Vector Generation**: Bedrock Titan creates embeddings
9. **Storage**: Content and vectors stored in S3
10. **Indexing**: Manifest updated for search and retrieval

### Security Features
- **End-to-end encryption** for data in transit and at rest
- **JWT authentication** with AWS Cognito
- **Role-based access control** (RBAC)
- **Audit logging** for compliance
- **Secure API endpoints** with rate limiting

### Scalability Features
- **Serverless architecture** with auto-scaling Lambda workers
- **Event-driven processing** via EventBridge
- **Multi-queue system** with priority handling
- **CloudWatch monitoring** and automated alerts

## Best Practices

### Document Processing
- **File Size**: Keep PDFs under 15MB for optimal processing
- **Content Quality**: Ensure good OCR quality for scanned documents
- **Naming**: Use descriptive job names for easy identification
- **Notes**: Use notes field for context, not content

### System Monitoring
- **Regular Checks**: Monitor dashboard daily for system health
- **Job Monitoring**: Review failed jobs promptly
- **Storage Usage**: Monitor S3 usage and plan for growth
- **Performance**: Watch processing times for optimization opportunities

### Security
- **Password Management**: Use strong, unique passwords
- **Session Management**: Log out when not using the system
- **Access Review**: Regularly review user permissions
- **Data Handling**: Handle sensitive documents appropriately

## Troubleshooting

### Common Issues

**Upload Failures**:
- Check file size limits (15MB)
- Verify PDF is not password-protected
- Ensure stable internet connection

**Processing Delays**:
- Large files take longer to process
- Check queue depth in dashboard
- Monitor Lambda worker status

**Search Issues**:
- Use at least 2 characters for search
- Check spelling and try variations
- Search works on metadata, not full content

**Authentication Problems**:
- Clear browser cache and cookies
- Check password expiration
- Contact admin for account issues

### Getting Help
1. Check this User Guide first
2. Review Diagnostics page for system status
3. Check Dashboard for real-time metrics
4. Contact system administrator for technical issues

## Support and Resources

- **Documentation**: Comprehensive guides in project repository
- **API Reference**: Interactive API docs at /docs endpoint
- **System Status**: Real-time monitoring via Dashboard
- **Logs**: CloudWatch logs for detailed troubleshooting

---

*This guide covers S3 Vector Store Ingestor version 0.77. Features and functionality may evolve with future updates.*