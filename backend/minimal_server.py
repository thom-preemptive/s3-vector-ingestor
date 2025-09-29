#!/usr/bin/env python3
"""
Minimal Emergency Document Processor API
For testing deployment without AWS dependencies.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import asyncio
import uuid
from datetime import datetime
import uvicorn

app = FastAPI(
    title="agent2_ingestor",
    description="Document processing system - Test Mode",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for testing
jobs_storage = {}
system_stats = {
    "total_jobs": 0,
    "completed_jobs": 0,
    "failed_jobs": 0,
    "pending_jobs": 0,
    "start_time": datetime.now().isoformat()
}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "agent2_ingestor API",
        "version": "1.0.0",
        "mode": "test",
        "status": "running",
        "description": "Test deployment without full AWS infrastructure"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": (datetime.now() - datetime.fromisoformat(system_stats["start_time"])).total_seconds(),
        "services": {
            "api": "online",
            "storage": "memory",
            "queue": "simulated",
            "aws": "disabled"
        },
        "mode": "test"
    }

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify API functionality"""
    return {
        "message": "API is working correctly!",
        "endpoints": {
            "health": "/health",
            "upload": "/upload/pdf",
            "process_urls": "/process/urls", 
            "jobs": "/jobs",
            "dashboard": "/dashboard/overview"
        },
        "test_completed": True
    }

@app.post("/upload/pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    job_name: str = Form(...),
    user_id: str = Form("test-user"),
    priority: int = Form(2),
    requires_approval: bool = Form(False)
):
    """Upload PDF for processing (simulated)"""
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    
    # Simulate processing
    job_data = {
        "job_id": job_id,
        "job_name": job_name,
        "user_id": user_id,
        "status": "completed",
        "source_type": "pdf",
        "source_data": file.filename,
        "priority": priority,
        "requires_approval": requires_approval,
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "metadata": {
            "file_size": file.size if hasattr(file, 'size') else 0,
            "content_type": file.content_type,
            "processing_time": "2.3s",
            "pages_processed": 5,
            "text_extracted": "Sample text content extracted from PDF",
            "vectors_generated": 42
        }
    }
    
    jobs_storage[job_id] = job_data
    system_stats["total_jobs"] += 1
    system_stats["completed_jobs"] += 1
    
    return {
        "message": "PDF uploaded and processed successfully",
        "job_id": job_id,
        "status": "completed",
        "result": {
            "markdown_stored": True,
            "vectors_generated": True,
            "approval_required": requires_approval
        }
    }

@app.post("/process/urls")
async def process_urls(
    urls: List[str],
    job_name: str,
    user_id: str = "test-user",
    priority: int = 2,
    requires_approval: bool = False
):
    """Process URLs (simulated)"""
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    
    # Simulate processing
    job_data = {
        "job_id": job_id,
        "job_name": job_name,
        "user_id": user_id,
        "status": "completed",
        "source_type": "urls",
        "source_data": urls,
        "priority": priority,
        "requires_approval": requires_approval,
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "metadata": {
            "urls_count": len(urls),
            "processing_time": "4.7s",
            "content_extracted": "Sample web content extracted from URLs",
            "vectors_generated": 156
        }
    }
    
    jobs_storage[job_id] = job_data
    system_stats["total_jobs"] += 1
    system_stats["completed_jobs"] += 1
    
    return {
        "message": f"Processed {len(urls)} URLs successfully",
        "job_id": job_id,
        "status": "completed",
        "urls_processed": len(urls)
    }

@app.get("/jobs")
async def get_jobs(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """Get jobs with filtering"""
    filtered_jobs = list(jobs_storage.values())
    
    if user_id:
        filtered_jobs = [job for job in filtered_jobs if job["user_id"] == user_id]
    
    if status:
        filtered_jobs = [job for job in filtered_jobs if job["status"] == status]
    
    return {
        "jobs": filtered_jobs[:limit],
        "total": len(filtered_jobs),
        "limit": limit
    }

@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get specific job details"""
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs_storage[job_id]

@app.get("/dashboard/overview")
async def dashboard_overview():
    """Dashboard overview with system statistics"""
    return {
        "system_health": {
            "status": "healthy",
            "score": 98,
            "uptime": (datetime.now() - datetime.fromisoformat(system_stats["start_time"])).total_seconds()
        },
        "job_statistics": system_stats,
        "queue_status": {
            "document_processing": {
                "pending": 0,
                "processing": 0,
                "dlq": 0
            },
            "approval_workflow": {
                "pending": 0,
                "processing": 0,
                "dlq": 0
            }
        },
        "performance": {
            "avg_processing_time": "3.2s",
            "throughput_per_hour": 45,
            "success_rate": 100.0
        },
        "mode": "test"
    }

@app.get("/dashboard/health")
async def dashboard_health():
    """Detailed system health"""
    return {
        "overall_status": "healthy",
        "health_score": 98,
        "components": {
            "api_server": {"status": "healthy", "response_time": "12ms"},
            "job_queue": {"status": "healthy", "simulated": True},
            "storage": {"status": "healthy", "type": "memory"},
            "processing": {"status": "healthy", "workers": "simulated"}
        },
        "alerts": [],
        "last_updated": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 agent2_ingestor - Test Server")
    print("=" * 50)
    print("📡 Server URL: http://localhost:8000")
    print("📋 API Docs: http://localhost:8000/docs")
    print("🏥 Health: http://localhost:8000/health")
    print("🧪 Test: http://localhost:8000/test")
    print("📊 Dashboard: http://localhost:8000/dashboard/overview")
    print("=" * 50)
    print("⚠️  Running in TEST MODE - AWS services simulated")
    print("✅ Ready for testing deployment and API functionality")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )