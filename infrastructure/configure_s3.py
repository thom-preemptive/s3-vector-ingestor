import boto3
import json
from datetime import datetime

def configure_s3_bucket():
    """Configure S3 bucket with proper structure and policies"""
    s3_client = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'emergency-docs-bucket-us-east-1'
    
    try:
        # Create folder structure by uploading placeholder files
        folders = [
            'documents/',
            'sidecars/', 
            'uploads/temp/',
            'processed/',
            'failed/'
        ]
        
        for folder in folders:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=folder + '.keep',
                Body=b'# This file maintains the folder structure'
            )
            print(f"Created folder: {folder}")
        
        # Create initial manifest.json
        initial_manifest = {
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "documents": [],
            "document_count": 0,
            "description": "Emergency Document Processor Manifest"
        }
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key='manifest.json',
            Body=json.dumps(initial_manifest, indent=2).encode('utf-8'),
            ContentType='application/json'
        )
        print("Created initial manifest.json")
        
        # Set up bucket lifecycle policy for temp files
        lifecycle_config = {
            'Rules': [
                {
                    'ID': 'TempFileCleanup',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'uploads/temp/'},
                    'Expiration': {'Days': 7}
                },
                {
                    'ID': 'FailedJobCleanup', 
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'failed/'},
                    'Expiration': {'Days': 30}
                }
            ]
        }
        
        s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration=lifecycle_config
        )
        print("Applied lifecycle policies")
        
        # Enable versioning for important files
        s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print("Enabled bucket versioning")
        
        print(f"S3 bucket {bucket_name} configured successfully!")
        
    except Exception as e:
        print(f"Error configuring S3 bucket: {e}")

if __name__ == "__main__":
    configure_s3_bucket()