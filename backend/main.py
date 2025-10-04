from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
import boto3
import json
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="agent2_ingestor",
    description="Serverless document processing system with AWS integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Import our services
from services.aws_services import S3Service, DynamoDBService, CognitoService
from services.approval_service import ApprovalService
from services.queue_service import JobQueueService, QueueType, JobPriority
from services.orchestration_service import EventBridgeService

# Import dashboard API
from dashboard_api import router as dashboard_router

# Initialize services
s3_service = S3Service()
dynamodb_service = DynamoDBService()
cognito_service = CognitoService()
approval_service = ApprovalService()
queue_service = JobQueueService()
eventbridge_service = EventBridgeService()

# Include dashboard router
app.include_router(dashboard_router)

# AWS clients (for backward compatibility)
s3_client = boto3.client('s3', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
textract_client = boto3.client('textract', region_name='us-east-1')
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

# Environment variables
S3_BUCKET = os.getenv("S3_BUCKET", "agent2-ingestor-bucket-us-east-1")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "document-jobs")
MANIFEST_KEY = os.getenv("MANIFEST_KEY", "manifest.json")

# Pydantic models
class DocumentRequest(BaseModel):
    urls: Optional[List[HttpUrl]] = None
    user_id: str
    job_name: str
    approval_required: bool = True

class JobStatus(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    user_id: str
    job_name: str
    documents_processed: int
    total_documents: int
    approval_status: Optional[str] = None

class ApprovalRequest(BaseModel):
    job_id: str
    approved: bool
    approver_id: str
    notes: Optional[str] = None

# Authentication models
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    id_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class CreateUserRequest(BaseModel):
    username: str
    email: str
    temporary_password: str
    name: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    username: str

class ConfirmPasswordRequest(BaseModel):
    username: str
    confirmation_code: str
    new_password: str

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Authentication dependency with Cognito JWT validation
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        # Extract the token from the Authorization header
        token = credentials.credentials
        
        # Verify the JWT token using Cognito (ID token verification)
        token_payload = await cognito_service.verify_token(token)
        
        # Extract user info from the token payload (ID token contains all necessary claims)
        # No need to call GetUser API since ID token has all the info we need
        return {
            "user_id": token_payload.get("sub"),
            "username": token_payload.get("cognito:username", token_payload.get("email")),
            "email": token_payload.get("email"),
            "token_payload": token_payload
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Dashboard Statistics Endpoints
@app.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics (total jobs, completed, pending, errors)"""
    try:
        # Get all jobs from DynamoDB
        all_jobs = await dynamodb_service.get_all_jobs()
        
        # Count jobs by status
        total_jobs = len(all_jobs)
        completed_jobs = sum(1 for job in all_jobs if job.get('status') == 'completed')
        pending_jobs = sum(1 for job in all_jobs if job.get('status') in ['queued', 'processing'])
        error_jobs = sum(1 for job in all_jobs if job.get('status') == 'failed')
        
        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "pending_jobs": pending_jobs,
            "error_jobs": error_jobs,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

@app.get("/dashboard/recent-jobs")
async def get_recent_jobs(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Get recent jobs for dashboard"""
    try:
        # Get all jobs and sort by created date
        all_jobs = await dynamodb_service.get_all_jobs()
        
        # Sort by created_at descending (most recent first)
        sorted_jobs = sorted(
            all_jobs,
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )
        
        # Take the most recent N jobs
        recent_jobs = sorted_jobs[:limit]
        
        # Format for dashboard
        formatted_jobs = []
        for job in recent_jobs:
            # Get document count from manifest if available
            documents_processed = 0
            if job.get('status') == 'completed':
                try:
                    # Count documents for this job from manifest
                    manifest = await s3_service.get_manifest()
                    documents_for_job = [
                        doc for doc in manifest.get('documents', [])
                        if doc.get('job_id') == job.get('job_id')
                    ]
                    documents_processed = len(documents_for_job)
                except Exception:
                    documents_processed = len(job.get('files', []))
            else:
                documents_processed = len(job.get('files', []))
            
            formatted_jobs.append({
                "id": job.get('job_id'),
                "name": job.get('job_name', 'Unnamed Job'),
                "status": job.get('status', 'unknown'),
                "documents_processed": documents_processed,
                "created_at": job.get('created_at', datetime.utcnow().isoformat())
            })
        
        return {
            "jobs": formatted_jobs,
            "total_count": len(all_jobs),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent jobs: {str(e)}")

# Authentication endpoints
@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user with username/password"""
    try:
        result = await cognito_service.authenticate_user(request.username, request.password)
        
        if 'challenge' in result:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "authentication_challenge",
                    "challenge": result['challenge'],
                    "message": "Additional authentication step required"
                }
            )
        
        return TokenResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    try:
        result = await cognito_service.refresh_token(request.refresh_token)
        return TokenResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/auth/create-user")
async def create_user(request: CreateUserRequest):
    """Create a new user (admin endpoint)"""
    try:
        result = await cognito_service.create_user(
            username=request.username,
            email=request.email,
            temporary_password=request.temporary_password,
            name=request.name or request.username
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Initiate password reset"""
    try:
        result = await cognito_service.reset_password(request.username)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/confirm-password")
async def confirm_password(request: ConfirmPasswordRequest):
    """Confirm password reset with verification code"""
    try:
        result = await cognito_service.confirm_forgot_password(
            request.username,
            request.confirmation_code,
            request.new_password
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user_id": current_user["user_id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "authenticated": True
    }

# Import the document processor
from services.document_processor import DocumentProcessor

# Initialize document processor
document_processor = DocumentProcessor()

# Get presigned URLs for direct S3 upload (for large files)
@app.post("/upload/presigned-url")
async def get_presigned_upload_url(
    filename: str = Form(...),
    content_type: str = Form("application/pdf"),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a presigned URL for direct upload to S3.
    This bypasses API Gateway's 10MB limit.
    """
    try:
        # Generate unique key for the file
        file_key = f"uploads/{current_user['user_id']}/{uuid.uuid4()}/{filename}"
        
        # Generate presigned URL (valid for 15 minutes)
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': file_key,
                'ContentType': content_type
            },
            ExpiresIn=900  # 15 minutes
        )
        
        return {
            "upload_url": presigned_url,
            "file_key": file_key,
            "expires_in": 900
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Upload PDF files
@app.post("/upload/pdf")
async def upload_pdf(
    files: List[UploadFile] = File(...),
    job_name: str = Form(...),
    approval_required: bool = Form(True),
    current_user: dict = Depends(get_current_user)
):
    job_id = str(uuid.uuid4())
    
    try:
        # Create job record in DynamoDB
        job_data = {
            'job_id': job_id,
            'user_id': current_user['user_id'],
            'job_name': job_name,
            'status': 'processing',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'total_documents': len(files),
            'documents_processed': 0,
            'approval_required': approval_required,
            'approval_status': 'pending' if approval_required else 'approved'
        }
        
        await dynamodb_service.create_job(job_data)
        
        # If approval is not required, process immediately
        if not approval_required:
            # Track user activity - job creation
            await approval_service.track_user_activity(
                user_id=current_user['user_id'],
                activity_type='job_created',
                metadata={
                    'job_id': job_id,
                    'file_count': len(files),
                    'job_name': job_name,
                    'approval_required': False
                }
            )
            
            # Read file contents
            file_contents = []
            filenames = []
            
            for file in files:
                content = await file.read()
                file_contents.append(content)
                filenames.append(file.filename)
            
            # Process documents in background
            try:
                processing_result = await document_processor.process_job(
                    job_id=job_id,
                    files=file_contents,
                    filenames=filenames,
                    user_id=current_user['user_id'],
                    job_name=job_name
                )
                
                # Track successful processing
                await approval_service.track_user_activity(
                    user_id=current_user['user_id'],
                    activity_type='documents_processed',
                    metadata={
                        'job_id': job_id,
                        'successful_documents': processing_result['successful_documents'],
                        'total_documents': processing_result['total_documents'],
                        'failed_documents': processing_result['failed_documents_count']
                    }
                )
                
                # Update job status
                await dynamodb_service.update_job_status(
                    job_id, 
                    'completed',
                    documents_processed=processing_result['successful_documents'],
                    processing_summary=f"Successfully processed {processing_result['successful_documents']} of {processing_result['total_documents']} documents"
                )
                
                return {
                    "job_id": job_id,
                    "status": "completed", 
                    "files_count": len(files),
                    "processing_result": processing_result
                }
                
            except Exception as e:
                # Track processing failure
                await approval_service.track_user_activity(
                    user_id=current_user['user_id'],
                    activity_type='processing_failed',
                    metadata={
                        'job_id': job_id,
                        'error': str(e)
                    }
                )
                
                # Mark job as failed
                await dynamodb_service.mark_job_failed(job_id, str(e))
                raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
        
        else:
            # Track user activity - job pending approval
            await approval_service.track_user_activity(
                user_id=current_user['user_id'],
                activity_type='job_created_pending_approval',
                metadata={
                    'job_id': job_id,
                    'file_count': len(files),
                    'job_name': job_name,
                    'approval_required': True
                }
            )
            
            # Job created, awaiting approval
            return {
                "job_id": job_id,
                "status": "pending_approval",
                "files_count": len(files),
                "message": "Job created successfully. Awaiting approval before processing."
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Process files that were uploaded to S3 via presigned URL
class S3UploadedFile(BaseModel):
    file_key: str
    filename: str

class S3UploadJobRequest(BaseModel):
    files: List[S3UploadedFile]
    job_name: str
    approval_required: bool = True

@app.post("/upload/process-s3-files")
async def process_s3_uploaded_files(
    request: S3UploadJobRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Process files that were uploaded directly to S3 via presigned URLs.
    
    Returns immediately with job_id. Processing happens asynchronously via EventBridge.
    """
    job_id = str(uuid.uuid4())
    
    try:
        # Determine initial status based on approval requirement
        initial_status = 'pending_approval' if request.approval_required else 'queued'
        
        # Create job record in DynamoDB
        job_data = {
            'job_id': job_id,
            'user_id': current_user['user_id'],
            'job_name': request.job_name,
            'status': initial_status,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'total_documents': len(request.files),
            'documents_processed': 0,
            'approval_required': request.approval_required,
            'approval_status': 'pending' if request.approval_required else 'approved'
        }
        
        await dynamodb_service.create_job(job_data)
        
        # If no approval required, send event to EventBridge for async processing
        if not request.approval_required:
            # Prepare file information for EventBridge
            files_info = [
                {
                    'file_key': f.file_key,
                    'filename': f.filename
                } 
                for f in request.files
            ]
            
            # Send event to EventBridge for async processing
            await eventbridge_service.send_document_processing_event(
                job_id=job_id,
                user_id=current_user['user_id'],
                files=files_info,
                job_name=request.job_name
            )
        
        return {
            "job_id": job_id,
            "status": initial_status,
            "files_count": len(request.files),
            "message": "Job created successfully. Processing in background - check Jobs page for status."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Process URLs
@app.post("/process/urls")
async def process_urls(
    request: DocumentRequest,
    current_user: dict = Depends(get_current_user)
):
    job_id = str(uuid.uuid4())
    
    try:
        # Validate URLs
        if not request.urls or len(request.urls) == 0:
            raise HTTPException(status_code=400, detail="No URLs provided")
        
        # Convert URLs to strings
        url_strings = [str(url) for url in request.urls]
        
        # Create job record in DynamoDB
        job_data = {
            'job_id': job_id,
            'user_id': current_user['user_id'],  # Use current user instead of request.user_id
            'job_name': request.job_name,
            'status': 'processing',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'total_documents': len(url_strings),
            'documents_processed': 0,
            'approval_required': request.approval_required,
            'approval_status': 'pending' if request.approval_required else 'approved'
        }
        
        await dynamodb_service.create_job(job_data)
        
        # If approval is not required, process immediately
        if not request.approval_required:
            try:
                processing_result = await document_processor.process_job(
                    job_id=job_id,
                    urls=url_strings,
                    user_id=current_user['user_id'],
                    job_name=request.job_name
                )
                
                # Update job status
                await dynamodb_service.update_job_status(
                    job_id,
                    'completed',
                    documents_processed=processing_result['successful_documents'],
                    processing_summary=f"Successfully processed {processing_result['successful_documents']} of {processing_result['total_documents']} URLs"
                )
                
                return {
                    "job_id": job_id,
                    "status": "completed",
                    "urls_count": len(url_strings),
                    "processing_result": processing_result
                }
                
            except Exception as e:
                # Mark job as failed
                await dynamodb_service.mark_job_failed(job_id, str(e))
                raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
        
        else:
            # Job created, awaiting approval
            return {
                "job_id": job_id,
                "status": "pending_approval",
                "urls_count": len(url_strings),
                "message": "Job created successfully. Awaiting approval before processing."
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get job status
@app.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    table = dynamodb.Table(DYNAMODB_TABLE)
    try:
        response = table.get_item(Key={'job_id': job_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = response['Item']
        return JobStatus(**job)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# List user jobs
@app.get("/jobs")
async def list_jobs(
    current_user: dict = Depends(get_current_user)
):
    table = dynamodb.Table(DYNAMODB_TABLE)
    try:
        response = table.scan(
            FilterExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': current_user['user_id']}
        )
        return {"jobs": response.get('Items', [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Approval workflow
@app.post("/approve")
async def approve_job(
    request: ApprovalRequest,
    current_user: dict = Depends(get_current_user)
):
    table = dynamodb.Table(DYNAMODB_TABLE)
    try:
        # Update job approval status
        table.update_item(
            Key={'job_id': request.job_id},
            UpdateExpression='SET approval_status = :status, approver_id = :approver, approval_notes = :notes, updated_at = :updated',
            ExpressionAttributeValues={
                ':status': 'approved' if request.approved else 'rejected',
                ':approver': request.approver_id,
                ':notes': request.notes or '',
                ':updated': datetime.utcnow().isoformat()
            }
        )
        
        # TODO: If approved, trigger manifest update and S3 upload
        
        return {"status": "success", "job_id": request.job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced job tracking endpoints
@app.get("/jobs/statistics")
async def get_job_statistics(
    current_user: dict = Depends(get_current_user)
):
    """Get job statistics for the current user"""
    try:
        stats = await dynamodb_service.get_job_statistics(current_user['user_id'])
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/pending-approvals")
async def list_pending_approvals(
    current_user: dict = Depends(get_current_user)
):
    """List all jobs pending approval (admin endpoint)"""
    try:
        # TODO: Add admin role check
        jobs = await dynamodb_service.list_pending_approvals()
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/status/{status}")
async def get_jobs_by_status(
    status: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all user jobs with a specific status"""
    try:
        all_jobs = await dynamodb_service.get_jobs_by_status(status)
        user_jobs = [job for job in all_jobs if job.get('user_id') == current_user['user_id']]
        return user_jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/jobs/{job_id}/progress")
async def update_job_progress(
    job_id: str,
    documents_processed: int,
    total_documents: int = None,
    status_message: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Update job progress"""
    try:
        await dynamodb_service.update_job_progress(
            job_id, documents_processed, total_documents, status_message
        )
        return {"status": "success", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/jobs/{job_id}/logs")
async def add_job_log(
    job_id: str,
    log_level: str,
    message: str,
    current_user: dict = Depends(get_current_user)
):
    """Add a log entry to a job"""
    try:
        await dynamodb_service.add_job_log(job_id, log_level, message)
        return {"status": "success", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Manifest management endpoints
@app.get("/manifest")
async def get_manifest(
    current_user: dict = Depends(get_current_user)
):
    """Get the current document manifest"""
    try:
        manifest = await s3_service.get_manifest()
        return manifest
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/manifest/search")
async def search_manifest(
    query: str = None,
    document_type: str = None,
    date_from: str = None,
    date_to: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Search documents in the manifest"""
    try:
        results = await s3_service.search_manifest(query, document_type, date_from, date_to)
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/manifest/statistics")
async def get_manifest_statistics(
    current_user: dict = Depends(get_current_user)
):
    """Get statistics about documents in the manifest"""
    try:
        stats = await s3_service.get_manifest_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/manifest/backup")
async def backup_manifest(
    current_user: dict = Depends(get_current_user)
):
    """Create a backup of the current manifest"""
    try:
        # TODO: Add admin role check
        backup_location = await s3_service.backup_manifest()
        return {"status": "success", "backup_location": backup_location}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/manifest/validate")
async def validate_manifest_integrity(
    current_user: dict = Depends(get_current_user)
):
    """Validate manifest integrity"""
    try:
        validation_results = await s3_service.validate_manifest_integrity()
        return validation_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===============================
# APPROVAL WORKFLOW ENDPOINTS
# ===============================

class ApprovalRequest(BaseModel):
    job_id: str
    request_reason: Optional[str] = None
    approval_deadline: Optional[str] = None

class ApprovalAction(BaseModel):
    approval_id: str
    comment: Optional[str] = None
    reason: Optional[str] = None

@app.post("/approvals/request")
async def create_approval_request(
    request: ApprovalRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new approval request for a job"""
    try:
        # Get job details to include in approval request
        job = await dynamodb_service.get_job(request.job_id)
        
        # Verify user owns the job
        if job.get('user_id') != current_user['sub']:
            raise HTTPException(status_code=403, detail="Not authorized to request approval for this job")
        
        # Extract document list from job
        document_list = job.get('processed_documents', [])
        
        # Parse deadline if provided
        deadline = None
        if request.approval_deadline:
            try:
                deadline = datetime.fromisoformat(request.approval_deadline.replace('Z', '+00:00'))
            except:
                raise HTTPException(status_code=400, detail="Invalid deadline format")
        
        approval_id = await approval_service.create_approval_request(
            job_id=request.job_id,
            user_id=current_user['sub'],
            document_list=document_list,
            request_reason=request.request_reason,
            approval_deadline=deadline
        )
        
        # Update job status to include approval request
        await dynamodb_service.update_job_status(
            request.job_id, 
            "awaiting_approval",
            approval_id=approval_id,
            approval_requested_at=datetime.utcnow().isoformat()
        )
        
        return {
            "status": "success",
            "approval_id": approval_id,
            "message": "Approval request created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/approvals/approve")
async def approve_request(
    action: ApprovalAction,
    current_user: dict = Depends(get_current_user)
):
    """Approve a pending request"""
    try:
        # TODO: Add role check for approvers
        result = await approval_service.approve_request(
            approval_id=action.approval_id,
            approver_id=current_user['sub'],
            comment=action.comment
        )
        
        # Update job status
        if result.get('job_id'):
            await dynamodb_service.update_job_status(
                result['job_id'], 
                "approved",
                approved_by=current_user['sub'],
                approved_at=result['approved_at']
            )
        
        return {
            "status": "success",
            "result": result,
            "message": "Request approved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/approvals/reject")
async def reject_request(
    action: ApprovalAction,
    current_user: dict = Depends(get_current_user)
):
    """Reject a pending request"""
    try:
        if not action.reason:
            raise HTTPException(status_code=400, detail="Reason is required for rejection")
        
        # TODO: Add role check for approvers
        result = await approval_service.reject_request(
            approval_id=action.approval_id,
            approver_id=current_user['sub'],
            reason=action.reason
        )
        
        # Update job status if job_id is available
        # Note: Need to get job_id from approval record
        try:
            # Get approval details to find job_id
            approvals = await approval_service.get_user_approval_history(current_user['sub'])
            approval = next((a for a in approvals if a['approval_id'] == action.approval_id), None)
            if approval and approval.get('job_id'):
                await dynamodb_service.update_job_status(
                    approval['job_id'], 
                    "rejected",
                    rejected_by=current_user['sub'],
                    rejected_at=result['rejected_at'],
                    rejection_reason=action.reason
                )
        except Exception as update_error:
            print(f"Warning: Failed to update job status: {update_error}")
        
        return {
            "status": "success",
            "result": result,
            "message": "Request rejected successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/approvals/pending")
async def get_pending_approvals(
    current_user: dict = Depends(get_current_user)
):
    """Get all pending approval requests"""
    try:
        # TODO: Add role check for approvers
        pending_approvals = await approval_service.get_pending_approvals()
        return {
            "status": "success",
            "pending_approvals": pending_approvals,
            "count": len(pending_approvals)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/approvals/history")
async def get_approval_history(
    current_user: dict = Depends(get_current_user)
):
    """Get approval history for current user"""
    try:
        history = await approval_service.get_user_approval_history(current_user['sub'])
        return {
            "status": "success",
            "approval_history": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/statistics")
async def get_user_statistics(
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive user statistics"""
    try:
        stats = await approval_service.get_user_statistics(current_user['sub'])
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/approvals")
async def get_approval_analytics(
    current_user: dict = Depends(get_current_user)
):
    """Get system-wide approval analytics (admin only)"""
    try:
        # TODO: Add admin role check
        analytics = await approval_service.get_approval_analytics()
        return {
            "status": "success",
            "analytics": analytics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===============================
# USER ACTIVITY TRACKING
# ===============================

@app.post("/users/activity")
async def track_user_activity(
    activity_type: str,
    metadata: Optional[dict] = None,
    current_user: dict = Depends(get_current_user)
):
    """Track user activity for analytics"""
    try:
        await approval_service.track_user_activity(
            user_id=current_user['sub'],
            activity_type=activity_type,
            metadata=metadata or {}
        )
        return {"status": "success", "message": "Activity tracked"}
    except Exception as e:
        # Don't fail the request if activity tracking fails
        print(f"Warning: Activity tracking failed: {str(e)}")
        return {"status": "warning", "message": "Activity tracking failed but request processed"}

# Queue-based Document Processing Endpoints

@app.post("/queue/process/pdf")
async def queue_pdf_processing(
    files: List[UploadFile] = File(...),
    job_name: str = Form(...),
    priority: int = Form(2),  # Default to normal priority
    approval_required: bool = Form(True),
    current_user: dict = Depends(get_current_user)
):
    """Queue PDF files for processing using the job queue system"""
    try:
        # Validate priority
        if priority not in [1, 2, 3, 4]:
            priority = 2  # Default to normal
        
        job_priority = JobPriority(priority)
        
        # Prepare file data for queue payload
        file_data = []
        for file in files:
            content = await file.read()
            file_data.append({
                'filename': file.filename,
                'content': content.decode('latin1'),  # Store as string for JSON
                'content_type': file.content_type
            })
        
        # Create queue payload
        payload = {
            'type': 'pdf_processing',
            'job_name': job_name,
            'files': file_data,
            'approval_required': approval_required,
            'created_by': current_user.get('sub'),
            'metadata': {
                'file_count': len(files),
                'total_size': sum(len(f['content']) for f in file_data)
            }
        }
        
        # Enqueue job
        job_id = await queue_service.enqueue_job(
            queue_type=QueueType.DOCUMENT_PROCESSING,
            payload=payload,
            user_id=current_user.get('sub'),
            priority=job_priority,
            estimated_duration=300  # 5 minutes estimated
        )
        
        return {
            "job_id": job_id,
            "message": "PDF processing job queued successfully",
            "priority": priority,
            "estimated_processing_time": "5-10 minutes"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue PDF processing: {str(e)}")

@app.post("/queue/process/urls")
async def queue_url_processing(
    request: DocumentRequest,
    priority: int = 2,  # Default to normal priority
    current_user: dict = Depends(get_current_user)
):
    """Queue URL processing using the job queue system"""
    try:
        # Validate URLs
        if not request.urls or len(request.urls) == 0:
            raise HTTPException(status_code=400, detail="No URLs provided")
        
        # Validate priority
        if priority not in [1, 2, 3, 4]:
            priority = 2  # Default to normal
        
        job_priority = JobPriority(priority)
        
        # Convert URLs to strings
        url_strings = [str(url) for url in request.urls]
        
        # Create queue payload
        payload = {
            'type': 'url_processing',
            'job_name': request.job_name,
            'urls': url_strings,
            'approval_required': request.approval_required,
            'created_by': current_user.get('sub'),
            'metadata': {
                'url_count': len(url_strings)
            }
        }
        
        # Enqueue job
        job_id = await queue_service.enqueue_job(
            queue_type=QueueType.DOCUMENT_PROCESSING,
            payload=payload,
            user_id=current_user.get('sub'),
            priority=job_priority,
            estimated_duration=len(url_strings) * 60  # 1 minute per URL estimated
        )
        
        return {
            "job_id": job_id,
            "message": "URL processing job queued successfully",
            "priority": priority,
            "estimated_processing_time": f"{len(url_strings) * 1} minutes"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue URL processing: {str(e)}")

@app.post("/queue/approval/{job_id}")
async def queue_approval_request(
    job_id: str,
    priority: int = 2,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Queue an approval request"""
    try:
        job_priority = JobPriority(min(4, max(1, priority)))
        
        # Create approval queue payload
        payload = {
            'type': 'approval_request',
            'job_id': job_id,
            'requester_id': current_user.get('sub'),
            'notes': notes,
            'metadata': {
                'requested_at': datetime.utcnow().isoformat()
            }
        }
        
        # Enqueue approval request
        approval_job_id = await queue_service.enqueue_job(
            queue_type=QueueType.APPROVAL_WORKFLOW,
            payload=payload,
            user_id=current_user.get('sub'),
            priority=job_priority,
            estimated_duration=30  # 30 seconds for approval processing
        )
        
        return {
            "approval_job_id": approval_job_id,
            "original_job_id": job_id,
            "message": "Approval request queued successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue approval request: {str(e)}")

@app.get("/queue/jobs/{job_id}/status")
async def get_queue_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the status of a queued job"""
    try:
        job = await queue_service.get_job_status(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if user owns the job (or is admin)
        if job.user_id != current_user.get('sub'):
            user_groups = current_user.get('cognito:groups', [])
            if 'admin' not in user_groups:
                raise HTTPException(status_code=403, detail="Not authorized to view this job")
        
        return job.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

@app.get("/queue/jobs")
async def get_user_queue_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get queue jobs for the current user"""
    try:
        from services.queue_service import JobStatus
        
        job_status = None
        if status:
            try:
                job_status = JobStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        jobs = await queue_service.get_user_jobs(
            user_id=current_user.get('sub'),
            status=job_status,
            limit=min(limit, 200)  # Max 200 jobs
        )
        
        return {
            "jobs": [job.to_dict() for job in jobs],
            "total_count": len(jobs),
            "user_id": current_user.get('sub')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user jobs: {str(e)}")

# ===================================
# Document Viewing and Search Endpoints
# ===================================
# NOTE: Order matters! Most specific routes must come first

@app.get("/documents/search")
async def search_documents(
    q: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    Search documents by filename, job name, or user ID.
    Returns matching documents with metadata.
    """
    try:
        if not q or len(q) < 2:
            raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
        
        results = await s3_service.search_documents(query=q, limit=limit)
        return {
            "query": q,
            "results": results,
            "count": len(results)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search documents: {str(e)}")

@app.get("/documents/manifest")
async def get_manifest(
    current_user: dict = Depends(get_current_user)
):
    """
    Get the complete document manifest with all metadata.
    """
    try:
        manifest = await s3_service.get_manifest()
        return manifest
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get manifest: {str(e)}")

@app.get("/documents/stats")
async def get_document_statistics(
    current_user: dict = Depends(get_current_user)
):
    """
    Get statistics about documents (total count, types, size, etc.)
    """
    try:
        stats = await s3_service.get_manifest_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@app.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    format: str = "markdown",
    current_user: dict = Depends(get_current_user)
):
    """
    Download document in specified format (markdown or json).
    Returns file content for download.
    """
    try:
        document = await s3_service.get_document_by_id(document_id)
        
        if format == "markdown":
            if not document.get('markdown_content'):
                raise HTTPException(status_code=404, detail="Markdown content not available")
            
            from fastapi.responses import Response
            return Response(
                content=document['markdown_content'],
                media_type="text/markdown",
                headers={
                    "Content-Disposition": f"attachment; filename={document.get('filename', 'document')}.md"
                }
            )
        
        elif format == "json":
            from fastapi.responses import JSONResponse
            return JSONResponse(
                content=document,
                headers={
                    "Content-Disposition": f"attachment; filename={document.get('filename', 'document')}.json"
                }
            )
        
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'markdown' or 'json'")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}")

@app.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get complete document information including markdown content and sidecar data.
    """
    try:
        document = await s3_service.get_document_by_id(document_id)
        return document
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

@app.get("/documents")
async def list_documents(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    List all documents with pagination.
    Returns document metadata without full content.
    """
    try:
        result = await s3_service.list_documents(limit=limit, offset=offset)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)