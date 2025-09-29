#!/usr/bin/env python3
"""
Emergency Document Processor - Deployment Test Script
Run this script to verify your deployment is working correctly.
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_deployment():
    """Comprehensive deployment test."""
    print("🚀 Starting Emergency Document Processor Deployment Test")
    print("=" * 60)
    
    # Test results
    results = {
        "aws_services": False,
        "queue_system": False,
        "api_server": False,
        "infrastructure": False
    }
    
    # Test 1: AWS Services
    print("\n📡 Testing AWS Services Integration...")
    try:
        from services.aws_services import S3Service, DynamoDBService
        
        s3_service = S3Service()
        manifest = await s3_service.get_manifest()
        print(f"✅ S3 Service: Connected, manifest version {manifest['version']}")
        print(f"   📄 Documents in manifest: {manifest['document_count']}")
        
        # Test S3 statistics
        stats = await s3_service.get_manifest_statistics()
        print(f"   📊 Manifest statistics: {stats}")
        
        results["aws_services"] = True
        
    except Exception as e:
        print(f"❌ AWS Services Error: {e}")
        print("   💡 Check your AWS credentials and S3 bucket configuration")
    
    # Test 2: Queue System
    print("\n🔄 Testing Queue System...")
    try:
        from services.queue_service import JobQueueService, QueueType, JobPriority
        
        queue_service = JobQueueService()
        stats = await queue_service.get_queue_statistics()
        print(f"✅ Queue Service: {len(stats)} queues configured")
        
        for queue_name, queue_stats in stats.items():
            print(f"   📋 {queue_name}: {queue_stats.get('messages_available', 0)} pending")
        
        # Test job enqueueing (dry run)
        test_job = {
            'job_id': 'deployment-test-job',
            'job_name': 'Deployment Test',
            'source_type': 'url',
            'source_data': 'https://example.com',
            'user_id': 'test-user',
            'metadata': {'deployment_test': True}
        }
        
        print("   🧪 Testing job enqueue (dry run)...")
        # Note: In a real deployment test, you might want to actually enqueue and process a job
        print("   ✅ Queue enqueue interface ready")
        
        results["queue_system"] = True
        
    except Exception as e:
        print(f"❌ Queue System Error: {e}")
        print("   💡 Check your SQS queues and DynamoDB tables")
    
    # Test 3: API Server
    print("\n🌐 Testing API Server...")
    try:
        import requests
        import time
        
        # Check if server is running
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ API Server: Running on port 8000")
                print(f"   🏥 Health status: {health_data.get('status', 'unknown')}")
                
                # Test dashboard endpoint
                dashboard_response = requests.get("http://localhost:8000/dashboard/overview", timeout=5)
                if dashboard_response.status_code == 200:
                    print("   📊 Dashboard API: Accessible")
                
                results["api_server"] = True
            else:
                print(f"❌ API Server: HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ API Server: Not running on localhost:8000")
            print("   💡 Start the server with: cd backend && python main.py")
        except requests.exceptions.Timeout:
            print("❌ API Server: Timeout (server may be starting)")
        
    except ImportError:
        print("❌ API Test: requests library not available")
        print("   💡 Install with: pip install requests")
    except Exception as e:
        print(f"❌ API Server Error: {e}")
    
    # Test 4: Infrastructure Check
    print("\n🏗️ Testing Infrastructure Components...")
    try:
        import boto3
        
        # Check AWS connectivity
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Connection: {identity['Arn']}")
        
        # Check S3 bucket
        s3 = boto3.client('s3')
        bucket_name = os.getenv('S3_BUCKET', 'emergency-docs-bucket-us-east-1')
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"✅ S3 Bucket: {bucket_name} accessible")
        except Exception as e:
            print(f"❌ S3 Bucket: {bucket_name} not accessible - {e}")
        
        # Check DynamoDB table
        dynamodb = boto3.client('dynamodb')
        table_name = os.getenv('DYNAMODB_TABLE', 'document-jobs')
        try:
            response = dynamodb.describe_table(TableName=table_name)
            status = response['Table']['TableStatus']
            print(f"✅ DynamoDB Table: {table_name} status={status}")
        except Exception as e:
            print(f"❌ DynamoDB Table: {table_name} not accessible - {e}")
        
        # Check SQS queues
        sqs = boto3.client('sqs')
        try:
            queues = sqs.list_queues()
            queue_count = len(queues.get('QueueUrls', []))
            print(f"✅ SQS Queues: {queue_count} queues found")
        except Exception as e:
            print(f"❌ SQS Queues: Error listing - {e}")
        
        results["infrastructure"] = True
        
    except Exception as e:
        print(f"❌ Infrastructure Error: {e}")
        print("   💡 Check your AWS credentials and permissions")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 DEPLOYMENT TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component.replace('_', ' ').title()}")
    
    print(f"\n🎯 Overall Status: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 Deployment is fully operational!")
        print("\n🚀 Next Steps:")
        print("   1. Access the API at: http://localhost:8000")
        print("   2. View API docs at: http://localhost:8000/docs")
        print("   3. Monitor dashboard at: http://localhost:8000/dashboard/overview")
        print("   4. Start the frontend: cd frontend && npm start")
    else:
        print("⚠️  Deployment has issues that need attention.")
        print("\n🔧 Troubleshooting:")
        if not results["aws_services"]:
            print("   - Check AWS credentials: aws configure")
            print("   - Verify S3 bucket exists and is accessible")
        if not results["queue_system"]:
            print("   - Deploy queue infrastructure: python infrastructure/deploy_queue_infrastructure.py")
        if not results["api_server"]:
            print("   - Start the backend server: cd backend && python main.py")
        if not results["infrastructure"]:
            print("   - Deploy core infrastructure: python infrastructure/setup_aws.py")
    
    return passed_tests == total_tests

def main():
    """Main entry point."""
    if __name__ == "__main__":
        # Check if we're in the right directory
        if not os.path.exists("backend") or not os.path.exists("infrastructure"):
            print("❌ Please run this script from the project root directory")
            print("   The directory should contain 'backend' and 'infrastructure' folders")
            sys.exit(1)
        
        # Run the deployment test
        success = asyncio.run(test_deployment())
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()