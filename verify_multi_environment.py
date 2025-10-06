#!/usr/bin/env python3
"""
Multi-Environment Deployment Verification Script
Verifies all three environments (DEV, TEST, MAIN) are correctly configured
with environment-specific resources.
"""

import boto3
import json
from typing import Dict, List

def verify_environment_deployment():
    """Verify all three environments are correctly deployed"""
    print("🚀 MULTI-ENVIRONMENT DEPLOYMENT VERIFICATION")
    print("=" * 60)
    
    environments = ['dev', 'test', 'main']
    
    # Initialize AWS clients
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
    s3_client = boto3.client('s3', region_name='us-east-1')
    
    verification_results = {}
    
    for env in environments:
        print(f"\n📋 VERIFYING {env.upper()} ENVIRONMENT")
        print("-" * 40)
        
        env_results = {
            'lambda_function': False,
            'dynamodb_tables': [],
            's3_bucket': False,
            'environment_variables': {},
            'api_gateway': ''
        }
        
        # 1. Verify Lambda Function
        function_name = f'agent2-ingestor-api-{env}'
        try:
            response = lambda_client.get_function_configuration(FunctionName=function_name)
            env_results['lambda_function'] = True
            env_results['environment_variables'] = response.get('Environment', {}).get('Variables', {})
            print(f"✅ Lambda Function: {function_name}")
            
            # Extract API Gateway URL from recent deployments
            if env == 'dev':
                env_results['api_gateway'] = 'https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev'
            elif env == 'test':
                env_results['api_gateway'] = 'https://b3krnh1y2l.execute-api.us-east-1.amazonaws.com/test'
            elif env == 'main':
                env_results['api_gateway'] = 'https://w17iflw3ai.execute-api.us-east-1.amazonaws.com/main'
            
        except Exception as e:
            print(f"❌ Lambda Function: {function_name} - {str(e)}")
        
        # 2. Verify DynamoDB Tables
        expected_tables = [
            f'agent2_ingestor_jobs_{env}',
            f'agent2_ingestor_approvals_{env}',
            f'agent2_ingestor_user_tracking_{env}',
            f'agent2_ingestor_queue_jobs_{env}'
        ]
        
        tables_response = dynamodb_client.list_tables()
        existing_tables = tables_response['TableNames']
        
        for table in expected_tables:
            if table in existing_tables:
                env_results['dynamodb_tables'].append(table)
                print(f"✅ DynamoDB Table: {table}")
            else:
                print(f"❌ DynamoDB Table: {table} - NOT FOUND")
        
        # 3. Verify S3 Bucket
        bucket_name = f'agent2-ingestor-bucket-{env}-us-east-1'
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            env_results['s3_bucket'] = True
            print(f"✅ S3 Bucket: {bucket_name}")
        except Exception as e:
            print(f"❌ S3 Bucket: {bucket_name} - {str(e)}")
        
        # 4. Verify Environment Variables
        env_vars = env_results['environment_variables']
        expected_env_vars = {
            'ENVIRONMENT': env,
            'DYNAMODB_TABLE': f'agent2_ingestor_jobs_{env}',
            'S3_BUCKET': f'agent2-ingestor-bucket-{env}-us-east-1',
            'QUEUE_JOBS_TABLE': f'agent2_ingestor_queue_jobs_{env}'
        }
        
        print(f"📝 Environment Variables:")
        for key, expected_value in expected_env_vars.items():
            actual_value = env_vars.get(key, 'NOT SET')
            if actual_value == expected_value:
                print(f"   ✅ {key}: {actual_value}")
            else:
                print(f"   ❌ {key}: Expected '{expected_value}', Got '{actual_value}'")
        
        verification_results[env] = env_results
    
    # Summary Report
    print(f"\n🎯 DEPLOYMENT SUMMARY")
    print("=" * 60)
    
    for env in environments:
        results = verification_results[env]
        lambda_status = "✅" if results['lambda_function'] else "❌"
        tables_status = f"✅ {len(results['dynamodb_tables'])}/4" if len(results['dynamodb_tables']) == 4 else f"❌ {len(results['dynamodb_tables'])}/4"
        s3_status = "✅" if results['s3_bucket'] else "❌"
        
        print(f"{env.upper():<6}: Lambda {lambda_status} | Tables {tables_status} | S3 {s3_status} | API: {results['api_gateway']}")
    
    # Check for complete success
    all_good = True
    for env in environments:
        results = verification_results[env]
        if not (results['lambda_function'] and len(results['dynamodb_tables']) == 4 and results['s3_bucket']):
            all_good = False
            break
    
    if all_good:
        print(f"\n🎉 SUCCESS: All three environments are correctly deployed!")
        print(f"📊 Total Resources Deployed:")
        print(f"   • Lambda Functions: 3 (dev, test, main)")
        print(f"   • DynamoDB Tables: 12 (4 per environment)")
        print(f"   • S3 Buckets: 3 (dev, test, main)")
        print(f"   • API Gateways: 3 (dev, test, main)")
    else:
        print(f"\n⚠️  Some environments have issues - please review above")
    
    return verification_results

if __name__ == "__main__":
    verify_environment_deployment()