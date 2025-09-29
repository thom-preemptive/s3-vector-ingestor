import json
import boto3
from typing import Dict, Any

def create_s3_bucket():
    """Create S3 bucket for document storage in US East-1"""
    s3_client = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'emergency-docs-bucket-us-east-1'
    
    try:
        # For us-east-1, don't specify LocationConstraint
        s3_client.create_bucket(Bucket=bucket_name)
        
        # Skip bucket policy for security - access will be managed through IAM
        print(f"S3 bucket {bucket_name} created successfully in US East-1")
        
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f"S3 bucket {bucket_name} already exists and is owned by you")
    except s3_client.exceptions.BucketAlreadyExists:
        print(f"S3 bucket {bucket_name} already exists")
    except Exception as e:
        print(f"Error creating S3 bucket: {e}")

def create_dynamodb_table():
    """Create DynamoDB table for job tracking in US East-1"""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    table_name = 'document-jobs'
    
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'job_id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'job_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'user_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for the table to be created
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        print(f"DynamoDB table {table_name} created successfully")
        
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print(f"DynamoDB table {table_name} already exists")
    except Exception as e:
        print(f"Error creating DynamoDB table: {e}")

def create_cognito_user_pool():
    """Create Cognito User Pool for authentication in US East-1"""
    cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
    
    try:
        # Create User Pool
        user_pool = cognito_client.create_user_pool(
            PoolName='emergency-doc-processor-users',
            Policies={
                'PasswordPolicy': {
                    'MinimumLength': 8,
                    'RequireUppercase': True,
                    'RequireLowercase': True,
                    'RequireNumbers': True,
                    'RequireSymbols': False
                }
            },
            AutoVerifiedAttributes=['email'],
            AliasAttributes=['email'],
            Schema=[
                {
                    'Name': 'email',
                    'AttributeDataType': 'String',
                    'Required': True,
                    'Mutable': True
                },
                {
                    'Name': 'name',
                    'AttributeDataType': 'String',
                    'Required': True,
                    'Mutable': True
                }
            ]
        )
        
        user_pool_id = user_pool['UserPool']['Id']
        
        # Create User Pool Client
        user_pool_client = cognito_client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName='emergency-doc-processor-client',
            GenerateSecret=False,
            ExplicitAuthFlows=['ADMIN_NO_SRP_AUTH', 'USER_PASSWORD_AUTH'],
            RefreshTokenValidity=30,  # days
            AccessTokenValidity=24,   # hours  
            IdTokenValidity=24        # hours
        )
        
        client_id = user_pool_client['UserPoolClient']['ClientId']
        
        print(f"Cognito User Pool created successfully:")
        print(f"User Pool ID: {user_pool_id}")
        print(f"Client ID: {client_id}")
        
        return user_pool_id, client_id
        
    except Exception as e:
        print(f"Error creating Cognito User Pool: {e}")
        return None, None

if __name__ == "__main__":
    print("Setting up AWS infrastructure...")
    
    create_s3_bucket()
    create_dynamodb_table()
    user_pool_id, client_id = create_cognito_user_pool()
    
    if user_pool_id and client_id:
        print(f"\nUpdate your .env file with:")
        print(f"COGNITO_USER_POOL_ID={user_pool_id}")
        print(f"COGNITO_CLIENT_ID={client_id}")
    
    print("\nInfrastructure setup completed!")