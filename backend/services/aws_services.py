import boto3
import json
from typing import Dict, Any, List
from datetime import datetime
import os

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name='us-east-1')
        self.bucket_name = os.getenv('S3_BUCKET', 'agent2-ingestor-bucket-us-east-1')
        self.manifest_key = os.getenv('MANIFEST_KEY', 'manifest.json')
    
    async def upload_document(self, content: str, key: str, metadata: Dict[str, Any] = None) -> str:
        """Upload document content to S3"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content.encode('utf-8'),
                ContentType='text/plain',
                Metadata=metadata or {}
            )
            return f"s3://{self.bucket_name}/{key}"
        except Exception as e:
            raise Exception(f"Failed to upload to S3: {str(e)}")
    
    async def upload_sidecar(self, sidecar_data: Dict[str, Any], key: str) -> str:
        """Upload vector sidecar file to S3"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(sidecar_data, indent=2).encode('utf-8'),
                ContentType='application/json'
            )
            return f"s3://{self.bucket_name}/{key}"
        except Exception as e:
            raise Exception(f"Failed to upload sidecar to S3: {str(e)}")
    
    async def update_manifest(self, document_entry: Dict[str, Any]) -> None:
        """Update the manifest.json file with new document entry"""
        try:
            # Try to get existing manifest
            try:
                response = self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=self.manifest_key
                )
                manifest = json.loads(response['Body'].read().decode('utf-8'))
            except self.s3_client.exceptions.NoSuchKey:
                # Create new manifest if it doesn't exist
                manifest = {
                    "version": "1.0",
                    "created_at": datetime.utcnow().isoformat(),
                    "documents": []
                }
            
            # Add new document entry
            manifest["documents"].append(document_entry)
            manifest["updated_at"] = datetime.utcnow().isoformat()
            manifest["document_count"] = len(manifest["documents"])
            
            # Upload updated manifest
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=self.manifest_key,
                Body=json.dumps(manifest, indent=2).encode('utf-8'),
                ContentType='application/json'
            )
            
        except Exception as e:
            raise Exception(f"Failed to update manifest: {str(e)}")
    
    async def get_manifest(self) -> Dict[str, Any]:
        """Get the current manifest"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=self.manifest_key
            )
            return json.loads(response['Body'].read().decode('utf-8'))
        except self.s3_client.exceptions.NoSuchKey:
            return {
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat(),
                "documents": [],
                "document_count": 0
            }
        except Exception as e:
            raise Exception(f"Failed to get manifest: {str(e)}")
    
    async def search_manifest(self, query: str = None, document_type: str = None, 
                            date_from: str = None, date_to: str = None) -> List[Dict[str, Any]]:
        """Search documents in the manifest"""
        try:
            manifest = await self.get_manifest()
            documents = manifest.get('documents', [])
            
            # Apply filters
            filtered_docs = documents
            
            if query:
                filtered_docs = [
                    doc for doc in filtered_docs 
                    if query.lower() in doc.get('filename', '').lower() or 
                       query.lower() in doc.get('job_name', '').lower()
                ]
            
            if document_type:
                filtered_docs = [
                    doc for doc in filtered_docs 
                    if doc.get('source_type') == document_type
                ]
            
            if date_from:
                filtered_docs = [
                    doc for doc in filtered_docs 
                    if doc.get('processed_at', '') >= date_from
                ]
            
            if date_to:
                filtered_docs = [
                    doc for doc in filtered_docs 
                    if doc.get('processed_at', '') <= date_to
                ]
            
            return filtered_docs
            
        except Exception as e:
            raise Exception(f"Failed to search manifest: {str(e)}")
    
    async def get_manifest_statistics(self) -> Dict[str, Any]:
        """Get statistics about documents in the manifest"""
        try:
            manifest = await self.get_manifest()
            documents = manifest.get('documents', [])
            
            stats = {
                'total_documents': len(documents),
                'pdf_documents': len([d for d in documents if d.get('source_type') == 'pdf']),
                'url_documents': len([d for d in documents if d.get('source_type') == 'url']),
                'total_size_bytes': sum(d.get('file_size', 0) for d in documents),
                'latest_upload': max([d.get('processed_at', '') for d in documents], default=''),
                'unique_users': len(set(d.get('user_id', '') for d in documents)),
                'unique_jobs': len(set(d.get('job_id', '') for d in documents))
            }
            
            return stats
            
        except Exception as e:
            raise Exception(f"Failed to get manifest statistics: {str(e)}")
    
    async def backup_manifest(self) -> str:
        """Create a backup of the current manifest"""
        try:
            manifest = await self.get_manifest()
            backup_key = f"backups/manifest_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=backup_key,
                Body=json.dumps(manifest, indent=2).encode('utf-8'),
                ContentType='application/json'
            )
            
            return f"s3://{self.bucket_name}/{backup_key}"
            
        except Exception as e:
            raise Exception(f"Failed to backup manifest: {str(e)}")
    
    async def validate_manifest_integrity(self) -> Dict[str, Any]:
        """Validate that all documents referenced in manifest exist in S3"""
        try:
            manifest = await self.get_manifest()
            documents = manifest.get('documents', [])
            
            validation_results = {
                'total_documents': len(documents),
                'valid_documents': 0,
                'missing_documents': [],
                'missing_sidecars': [],
                'errors': []
            }
            
            for doc in documents:
                markdown_key = doc.get('markdown_s3_key')
                sidecar_key = doc.get('sidecar_s3_key')
                
                # Check markdown file
                if markdown_key:
                    try:
                        self.s3_client.head_object(Bucket=self.bucket_name, Key=markdown_key)
                        validation_results['valid_documents'] += 1
                    except self.s3_client.exceptions.NoSuchKey:
                        validation_results['missing_documents'].append(markdown_key)
                
                # Check sidecar file
                if sidecar_key:
                    try:
                        self.s3_client.head_object(Bucket=self.bucket_name, Key=sidecar_key)
                    except self.s3_client.exceptions.NoSuchKey:
                        validation_results['missing_sidecars'].append(sidecar_key)
            
            return validation_results
            
        except Exception as e:
            validation_results['errors'].append(str(e))
            return validation_results
    
    async def get_document_content(self, s3_key: str) -> str:
        """Retrieve document content from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body'].read().decode('utf-8')
        except self.s3_client.exceptions.NoSuchKey:
            raise Exception(f"Document not found: {s3_key}")
        except Exception as e:
            raise Exception(f"Failed to retrieve document: {str(e)}")
    
    async def get_sidecar_data(self, s3_key: str) -> Dict[str, Any]:
        """Retrieve sidecar/vector data from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return json.loads(response['Body'].read().decode('utf-8'))
        except self.s3_client.exceptions.NoSuchKey:
            raise Exception(f"Sidecar not found: {s3_key}")
        except Exception as e:
            raise Exception(f"Failed to retrieve sidecar: {str(e)}")
    
    async def get_document_by_id(self, document_id: str) -> Dict[str, Any]:
        """Get complete document information including content and sidecar"""
        try:
            manifest = await self.get_manifest()
            documents = manifest.get('documents', [])
            
            # Find document by ID
            document = next((d for d in documents if d.get('document_id') == document_id), None)
            if not document:
                raise Exception(f"Document not found: {document_id}")
            
            # Get markdown content
            markdown_content = None
            if document.get('markdown_s3_key'):
                try:
                    markdown_content = await self.get_document_content(document['markdown_s3_key'])
                except Exception as e:
                    print(f"Warning: Could not load markdown content: {e}")
            
            # Get sidecar data
            sidecar_data = None
            if document.get('sidecar_s3_key'):
                try:
                    sidecar_data = await self.get_sidecar_data(document['sidecar_s3_key'])
                except Exception as e:
                    print(f"Warning: Could not load sidecar data: {e}")
            
            return {
                **document,
                'markdown_content': markdown_content,
                'sidecar_data': sidecar_data
            }
        except Exception as e:
            raise Exception(f"Failed to get document: {str(e)}")
    
    async def list_documents(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """List documents with pagination"""
        try:
            manifest = await self.get_manifest()
            documents = manifest.get('documents', [])
            
            # Sort by processed_at descending (newest first)
            sorted_docs = sorted(
                documents, 
                key=lambda x: x.get('processed_at', ''), 
                reverse=True
            )
            
            # Apply pagination
            paginated_docs = sorted_docs[offset:offset + limit]
            
            return {
                'documents': paginated_docs,
                'total': len(documents),
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < len(documents)
            }
        except Exception as e:
            raise Exception(f"Failed to list documents: {str(e)}")
    
    async def search_documents(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search documents by filename, job name, or content metadata"""
        try:
            manifest = await self.get_manifest()
            documents = manifest.get('documents', [])
            
            query_lower = query.lower()
            matching_docs = []
            
            for doc in documents:
                # Search in filename
                if query_lower in doc.get('filename', '').lower():
                    matching_docs.append({**doc, 'match_field': 'filename'})
                    continue
                
                # Search in job name
                if query_lower in doc.get('job_name', '').lower():
                    matching_docs.append({**doc, 'match_field': 'job_name'})
                    continue
                
                # Search in user_id
                if query_lower in doc.get('user_id', '').lower():
                    matching_docs.append({**doc, 'match_field': 'user_id'})
                    continue
            
            # Sort by processed_at descending
            matching_docs.sort(key=lambda x: x.get('processed_at', ''), reverse=True)
            
            return matching_docs[:limit]
        except Exception as e:
            raise Exception(f"Failed to search documents: {str(e)}")

    async def clear_environment_buckets(self, environment: str) -> List[str]:
        """
        Clear all objects from buckets belonging to the specified environment.
        Only works for DEV and TEST environments for safety.
        """
        if environment.lower() == 'main':
            raise Exception("Cannot clear buckets in MAIN environment")
        
        try:
            cleared_buckets = []
            
            # List all buckets
            response = self.s3_client.list_buckets()
            
            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                
                # Check if bucket belongs to this environment
                if f'-{environment}-' in bucket_name or bucket_name.endswith(f'-{environment}'):
                    # Clear all objects in the bucket
                    paginator = self.s3_client.get_paginator('list_objects_v2')
                    pages = paginator.paginate(Bucket=bucket_name)
                    
                    for page in pages:
                        if 'Contents' in page:
                            objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]
                            if objects_to_delete:
                                self.s3_client.delete_objects(
                                    Bucket=bucket_name,
                                    Delete={'Objects': objects_to_delete}
                                )
                    
                    cleared_buckets.append(bucket_name)
            
            return cleared_buckets
        except Exception as e:
            raise Exception(f"Failed to clear environment buckets: {str(e)}")

    async def get_total_document_count(self) -> int:
        """Get total count of documents across all environments"""
        try:
            manifest = await self.get_manifest()
            return len(manifest.get('documents', []))
        except Exception as e:
            return 0

    async def get_total_storage_usage_gb(self) -> float:
        """Get total storage usage in GB across all buckets"""
        try:
            total_size = 0
            response = self.s3_client.list_buckets()
            
            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                try:
                    paginator = self.s3_client.get_paginator('list_objects_v2')
                    pages = paginator.paginate(Bucket=bucket_name)
                    
                    for page in pages:
                        if 'Contents' in page:
                            for obj in page['Contents']:
                                total_size += obj.get('Size', 0)
                except:
                    continue  # Skip inaccessible buckets
            
            return round(total_size / (1024**3), 2)  # Convert to GB
        except Exception as e:
            return 0.0

class DynamoDBService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        # Get environment from env var (default to 'dev' if not set)
        self.environment = os.getenv('ENVIRONMENT', 'dev').lower()

        # Define base table names
        self.base_tables = {
            'jobs': 'agent2_ingestor_jobs'
        }

        # Apply environment suffix
        self.tables = {
            key: f"{name}_{self.environment}"
            for key, name in self.base_tables.items()
        }

        # Set the main jobs table
        self.table_name = self.tables['jobs']
        self.table = self.dynamodb.Table(self.table_name)
    
    async def create_job(self, job_data: Dict[str, Any]) -> str:
        """Create a new job record"""
        try:
            self.table.put_item(Item=job_data)
            return job_data['job_id']
        except Exception as e:
            raise Exception(f"Failed to create job: {str(e)}")
    
    async def update_job_status(self, job_id: str, status: str, **kwargs) -> None:
        """Update job status and other fields"""
        try:
            update_expression = "SET #status = :status, updated_at = :updated"
            expression_values = {
                ':status': status,
                ':updated': datetime.utcnow().isoformat()
            }
            expression_names = {'#status': 'status'}
            
            # Add any additional fields to update
            for key, value in kwargs.items():
                update_expression += f", {key} = :{key}"
                expression_values[f":{key}"] = value
            
            self.table.update_item(
                Key={'job_id': job_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_names
            )
        except Exception as e:
            raise Exception(f"Failed to update job status: {str(e)}")
    
    async def get_job(self, job_id: str) -> Dict[str, Any]:
        """Get job details"""
        try:
            response = self.table.get_item(Key={'job_id': job_id})
            if 'Item' not in response:
                raise Exception("Job not found")
            return response['Item']
        except Exception as e:
            raise Exception(f"Failed to get job: {str(e)}")
    
    async def list_user_jobs(self, user_id: str) -> List[Dict[str, Any]]:
        """List all jobs for a user"""
        try:
            response = self.table.scan(
                FilterExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id}
            )
            return response.get('Items', [])
        except Exception as e:
            raise Exception(f"Failed to list user jobs: {str(e)}")
    
    async def list_pending_approvals(self) -> List[Dict[str, Any]]:
        """List all jobs pending approval"""
        try:
            response = self.table.scan(
                FilterExpression='approval_status = :status',
                ExpressionAttributeValues={':status': 'pending'}
            )
            return response.get('Items', [])
        except Exception as e:
            raise Exception(f"Failed to list pending approvals: {str(e)}")
    
    async def get_job_statistics(self, user_id: str = None) -> Dict[str, Any]:
        """Get job statistics for a user or globally"""
        try:
            if user_id:
                response = self.table.scan(
                    FilterExpression='user_id = :user_id',
                    ExpressionAttributeValues={':user_id': user_id}
                )
            else:
                response = self.table.scan()
            
            jobs = response.get('Items', [])
            stats = {
                'total_jobs': len(jobs),
                'completed': len([j for j in jobs if j.get('status') == 'completed']),
                'processing': len([j for j in jobs if j.get('status') == 'processing']),
                'failed': len([j for j in jobs if j.get('status') == 'failed']),
                'pending_approval': len([j for j in jobs if j.get('approval_status') == 'pending']),
                'approved': len([j for j in jobs if j.get('approval_status') == 'approved']),
                'rejected': len([j for j in jobs if j.get('approval_status') == 'rejected'])
            }
            return stats
        except Exception as e:
            raise Exception(f"Failed to get job statistics: {str(e)}")
    
    async def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs from DynamoDB"""
        try:
            response = self.table.scan()
            return response.get('Items', [])
        except Exception as e:
            raise Exception(f"Failed to get all jobs: {str(e)}")
    
    async def update_job_progress(self, job_id: str, documents_processed: int, 
                                 total_documents: int = None, status_message: str = None) -> None:
        """Update job progress tracking"""
        try:
            update_expression = "SET documents_processed = :processed, updated_at = :updated"
            expression_values = {
                ':processed': documents_processed,
                ':updated': datetime.utcnow().isoformat()
            }
            
            if total_documents is not None:
                update_expression += ", total_documents = :total"
                expression_values[':total'] = total_documents
            
            if status_message:
                update_expression += ", status_message = :message"
                expression_values[':message'] = status_message
            
            self.table.update_item(
                Key={'job_id': job_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
        except Exception as e:
            raise Exception(f"Failed to update job progress: {str(e)}")
    
    async def add_job_log(self, job_id: str, log_level: str, message: str) -> None:
        """Add a log entry to a job"""
        try:
            # Get current logs
            job = await self.get_job(job_id)
            logs = job.get('logs', [])
            
            # Add new log entry
            logs.append({
                'timestamp': datetime.utcnow().isoformat(),
                'level': log_level,
                'message': message
            })
            
            # Keep only last 100 log entries
            if len(logs) > 100:
                logs = logs[-100:]
            
            self.table.update_item(
                Key={'job_id': job_id},
                UpdateExpression='SET logs = :logs, updated_at = :updated',
                ExpressionAttributeValues={
                    ':logs': logs,
                    ':updated': datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            raise Exception(f"Failed to add job log: {str(e)}")
    
    async def mark_job_failed(self, job_id: str, error_message: str) -> None:
        """Mark a job as failed with error details"""
        try:
            await self.update_job_status(
                job_id, 
                'failed', 
                error_message=error_message,
                failed_at=datetime.utcnow().isoformat()
            )
            await self.add_job_log(job_id, 'ERROR', error_message)
        except Exception as e:
            raise Exception(f"Failed to mark job as failed: {str(e)}")
    
    async def get_jobs_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all jobs with a specific status"""
        try:
            response = self.table.scan(
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': status}
            )
            return response.get('Items', [])
        except Exception as e:
            raise Exception(f"Failed to get jobs by status: {str(e)}")

    async def clear_environment_tables(self, environment: str) -> List[str]:
        """
        Clear all items from DynamoDB tables belonging to the specified environment.
        Only works for DEV and TEST environments for safety.
        """
        if environment.lower() == 'main':
            raise Exception("Cannot clear tables in MAIN environment")
        
        try:
            cleared_tables = []
            
            # List all tables
            paginator = self.dynamodb.meta.client.get_paginator('list_tables')
            
            for page in paginator.paginate():
                for table_name in page['TableNames']:
                    # Check if table belongs to this environment
                    if f'-{environment}-' in table_name or table_name.endswith(f'-{environment}'):
                        # Scan and delete all items in the table
                        table = self.dynamodb.Table(table_name)
                        
                        # Get table key schema to identify primary key
                        table_desc = table.meta.client.describe_table(TableName=table_name)
                        key_schema = table_desc['Table']['KeySchema']
                        
                        # Extract primary key attributes
                        key_attrs = [key['AttributeName'] for key in key_schema]
                        
                        # Scan all items
                        response = table.scan(ProjectionExpression=','.join(key_attrs))
                        
                        # Delete items in batches
                        with table.batch_writer() as batch:
                            for item in response['Items']:
                                key = {attr: item[attr] for attr in key_attrs}
                                batch.delete_item(Key=key)
                        
                        # Handle pagination
                        while 'LastEvaluatedKey' in response:
                            response = table.scan(
                                ProjectionExpression=','.join(key_attrs),
                                ExclusiveStartKey=response['LastEvaluatedKey']
                            )
                            with table.batch_writer() as batch:
                                for item in response['Items']:
                                    key = {attr: item[attr] for attr in key_attrs}
                                    batch.delete_item(Key=key)
                        
                        cleared_tables.append(table_name)
            
            return cleared_tables
        except Exception as e:
            raise Exception(f"Failed to clear environment tables: {str(e)}")

    async def get_total_job_count(self) -> int:
        """Get total count of jobs across all environments"""
        try:
            response = self.table.scan(Select='COUNT')
            return response.get('Count', 0)
        except Exception as e:
            return 0

    async def get_job_count_by_status(self, status: str) -> int:
        """Get count of jobs by status"""
        try:
            response = self.table.scan(
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': status},
                Select='COUNT'
            )
            return response.get('Count', 0)
        except Exception as e:
            return 0

class CognitoService:
    def __init__(self):
        self.cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
        self.user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
        self.client_id = os.getenv('COGNITO_CLIENT_ID')
        
        if not self.user_pool_id or not self.client_id:
            raise Exception("Cognito User Pool ID and Client ID must be configured")
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return user information"""
        try:
            # Import here to avoid circular imports
            from jose import jwt, JWTError
            import requests
            
            # Get the JWKS (JSON Web Key Set) from Cognito
            jwks_url = f"https://cognito-idp.{os.getenv('AWS_DEFAULT_REGION', 'us-east-1')}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
            jwks = requests.get(jwks_url).json()
            
            # Decode and verify the token
            headers = jwt.get_unverified_headers(token)
            kid = headers['kid']
            
            # Find the correct key
            key = None
            for jwk in jwks['keys']:
                if jwk['kid'] == kid:
                    key = jwk
                    break
            
            if not key:
                raise Exception("Public key not found")
            
            # Verify the token
            payload = jwt.decode(
                token,
                key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer=f"https://cognito-idp.{os.getenv('AWS_DEFAULT_REGION', 'us-east-1')}.amazonaws.com/{self.user_pool_id}"
            )
            
            return payload
            
        except JWTError as e:
            raise Exception(f"Invalid token: {str(e)}")
        except Exception as e:
            raise Exception(f"Token verification failed: {str(e)}")
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from access token"""
        try:
            response = self.cognito_client.get_user(AccessToken=access_token)
            
            # Convert attributes to a more usable format
            user_attributes = {}
            for attr in response['UserAttributes']:
                user_attributes[attr['Name']] = attr['Value']
            
            return {
                'username': response['Username'],
                'user_status': response['UserStatus'],
                'attributes': user_attributes,
                'user_id': user_attributes.get('sub', response['Username'])
            }
            
        except Exception as e:
            raise Exception(f"Failed to get user info: {str(e)}")
    
    async def create_user(self, username: str, email: str, temporary_password: str, **kwargs) -> Dict[str, Any]:
        """Create a new user in Cognito User Pool (admin function)"""
        try:
            response = self.cognito_client.admin_create_user(
                UserPoolId=self.user_pool_id,
                Username=username,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'email_verified', 'Value': 'true'},
                    *[{'Name': k, 'Value': v} for k, v in kwargs.items()]
                ],
                TemporaryPassword=temporary_password,
                MessageAction='SUPPRESS'  # Don't send welcome email
            )
            
            return {
                'username': response['User']['Username'],
                'user_status': response['User']['UserStatus'],
                'created': True
            }
            
        except Exception as e:
            raise Exception(f"Failed to create user: {str(e)}")
    
    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user with username/password"""
        try:
            response = self.cognito_client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            
            if 'ChallengeName' in response:
                # Handle challenges (e.g., password reset required)
                return {
                    'challenge': response['ChallengeName'],
                    'session': response['Session'],
                    'challenge_parameters': response.get('ChallengeParameters', {})
                }
            
            # Successful authentication
            auth_result = response['AuthenticationResult']
            return {
                'access_token': auth_result['AccessToken'],
                'id_token': auth_result['IdToken'],
                'refresh_token': auth_result['RefreshToken'],
                'token_type': auth_result['TokenType'],
                'expires_in': auth_result['ExpiresIn']
            }
            
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            response = self.cognito_client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': refresh_token
                }
            )
            
            auth_result = response['AuthenticationResult']
            return {
                'access_token': auth_result['AccessToken'],
                'id_token': auth_result['IdToken'],
                'token_type': auth_result['TokenType'],
                'expires_in': auth_result['ExpiresIn']
            }
            
        except Exception as e:
            raise Exception(f"Token refresh failed: {str(e)}")
    
    async def reset_password(self, username: str) -> Dict[str, Any]:
        """Initiate password reset for user"""
        try:
            response = self.cognito_client.admin_reset_user_password(
                UserPoolId=self.user_pool_id,
                Username=username
            )
            
            return {'message': 'Password reset initiated', 'success': True}
            
        except Exception as e:
            raise Exception(f"Password reset failed: {str(e)}")
    
    async def confirm_forgot_password(self, username: str, confirmation_code: str, new_password: str) -> Dict[str, Any]:
        """Confirm forgot password with verification code"""
        try:
            response = self.cognito_client.confirm_forgot_password(
                ClientId=self.client_id,
                Username=username,
                ConfirmationCode=confirmation_code,
                Password=new_password
            )
            
            return {'message': 'Password reset confirmed', 'success': True}
            
        except Exception as e:
            raise Exception(f"Password confirmation failed: {str(e)}")

    async def list_all_users(self) -> List[Dict[str, Any]]:
        """List all users in the user pool (admin only)"""
        try:
            users = []
            paginator = self.cognito_client.get_paginator('list_users')
            
            for page in paginator.paginate(UserPoolId=self.user_pool_id):
                for user in page['Users']:
                    user_data = {
                        'username': user['Username'],
                        'email': next((attr['Value'] for attr in user.get('Attributes', []) if attr['Name'] == 'email'), ''),
                        'status': user['UserStatus'],
                        'enabled': user['Enabled'],
                        'created': user['UserCreateDate'].isoformat(),
                        'last_modified': user['UserLastModifiedDate'].isoformat(),
                        'role': next((attr['Value'] for attr in user.get('Attributes', []) if attr['Name'] == 'custom:role'), 'user')
                    }
                    users.append(user_data)
            
            return users
        except Exception as e:
            raise Exception(f"Failed to list users: {str(e)}")

    async def get_user_count(self) -> int:
        """Get total count of users"""
        try:
            count = 0
            paginator = self.cognito_client.get_paginator('list_users')
            
            for page in paginator.paginate(UserPoolId=self.user_pool_id):
                count += len(page['Users'])
            
            return count
        except Exception as e:
            return 0

    async def get_active_users_count(self, days: int) -> int:
        """Get count of users active in the last N days"""
        try:
            # This is a simplified implementation
            # In a real scenario, you'd track user activity in DynamoDB
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            count = 0
            paginator = self.cognito_client.get_paginator('list_users')
            
            for page in paginator.paginate(UserPoolId=self.user_pool_id):
                for user in page['Users']:
                    if user['UserLastModifiedDate'] > cutoff_date:
                        count += 1
            
            return count
        except Exception as e:
            return 0

    async def get_new_users_count(self, days: int) -> int:
        """Get count of new users in the last N days"""
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            count = 0
            paginator = self.cognito_client.get_paginator('list_users')
            
            for page in paginator.paginate(UserPoolId=self.user_pool_id):
                for user in page['Users']:
                    if user['UserCreateDate'] > cutoff_date:
                        count += 1
            
            return count
        except Exception as e:
            return 0