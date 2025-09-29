#!/usr/bin/env python3
"""
Simple test server for Emergency Document Processor
Runs with minimal AWS dependencies for testing.
"""

import os
import sys
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add backend to path
sys.path.append(os.path.dirname(__file__))

# Set basic environment variables
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("S3_BUCKET", "emergency-docs-bucket-us-east-1")
os.environ.setdefault("DYNAMODB_TABLE", "document-jobs")

# Create simple FastAPI app
app = FastAPI(
    title="Emergency Document Processor",
    description="Emergency document processing system",
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

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Emergency Document Processor API",
        "version": "1.0.0",
        "status": "running",
        "environment": "development"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": str(asyncio.get_event_loop().time()),
        "services": {
            "api": "online",
            "aws": "configuring"
        }
    }

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {
        "message": "API is working!",
        "environment_variables": {
            "AWS_REGION": os.getenv("AWS_REGION"),
            "S3_BUCKET": os.getenv("S3_BUCKET"),
            "DYNAMODB_TABLE": os.getenv("DYNAMODB_TABLE")
        }
    }

# Try to add dashboard routes if available
try:
    from dashboard_api import router as dashboard_router
    app.include_router(dashboard_router)
    print("✅ Dashboard API routes loaded")
except Exception as e:
    print(f"⚠️  Dashboard API not available: {e}")

# Try to add main API routes if available
try:
    from main import app as main_app
    # Copy routes from main app
    for route in main_app.routes:
        if hasattr(route, 'path') and route.path not in ["/", "/health", "/test"]:
            app.routes.append(route)
    print("✅ Main API routes loaded")
except Exception as e:
    print(f"⚠️  Main API not fully available: {e}")

if __name__ == "__main__":
    print("🚀 Starting Emergency Document Processor Test Server")
    print("=" * 50)
    print("📡 Server will be available at: http://localhost:8000")
    print("📋 API Documentation at: http://localhost:8000/docs")
    print("🏥 Health Check at: http://localhost:8000/health")
    print("🧪 Test Endpoint at: http://localhost:8000/test")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )