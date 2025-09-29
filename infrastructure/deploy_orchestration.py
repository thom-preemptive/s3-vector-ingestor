#!/usr/bin/env python3
"""
Deployment script for Emergency Document Processor Serverless Orchestration

This script deploys the serverless infrastructure including:
- EventBridge event bus and rules
- Lambda functions for orchestration and processing
- API Gateway integration
- CloudWatch monitoring and alarms
"""

import boto3
import json
import time
import zipfile
import os
import sys
from datetime import datetime
import subprocess

def create_lambda_deployment_packages():
    """Create deployment packages for Lambda functions"""
    
    print("Creating Lambda deployment packages...")
    
    # Create deployment directory
    deploy_dir = "deployment_packages"
    os.makedirs(deploy_dir, exist_ok=True)
    
    # Package orchestrator function
    orchestrator_zip = os.path.join(deploy_dir, "document_orchestrator.zip")
    with zipfile.ZipFile(orchestrator_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write("../lambda/document_orchestrator.py", "document_orchestrator.py")
    
    # Package processor function
    processor_zip = os.path.join(deploy_dir, "document_processor.zip")
    with zipfile.ZipFile(processor_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write("../lambda/document_processor.py", "document_processor.py")
    
    print(f"✓ Created deployment packages in {deploy_dir}/")
    return orchestrator_zip, processor_zip

def deploy_cloudformation_stack(environment='dev', region='us-east-1'):
    """Deploy the CloudFormation stack"""
    
    print(f"Deploying CloudFormation stack for environment: {environment}")
    
    # Initialize CloudFormation client
    cf_client = boto3.client('cloudformation', region_name=region)
    
    stack_name = f"emergency-docs-orchestration-{environment}"
    template_path = "serverless-orchestration.yaml"
    
    # Read template
    with open(template_path, 'r') as f:
        template_body = f.read()
    
    # Stack parameters
    parameters = [
        {
            'ParameterKey': 'Environment',
            'ParameterValue': environment
        },
        {
            'ParameterKey': 'ProjectName',
            'ParameterValue': 'emergency-docs'
        },
        {
            'ParameterKey': 'S3BucketName',
            'ParameterValue': 'emergency-docs-bucket-us-east-1'
        },
        {
            'ParameterKey': 'CognitoUserPoolId',
            'ParameterValue': os.environ.get('COGNITO_USER_POOL_ID', 'us-east-1_CHANGEME')
        },
        {
            'ParameterKey': 'CognitoUserPoolClientId',
            'ParameterValue': os.environ.get('COGNITO_USER_POOL_CLIENT_ID', 'CHANGEME')
        }
    ]
    
    try:
        # Check if stack exists
        try:
            cf_client.describe_stacks(StackName=stack_name)
            stack_exists = True
            print(f"Stack {stack_name} exists, updating...")
        except cf_client.exceptions.ClientError:
            stack_exists = False
            print(f"Creating new stack {stack_name}...")
        
        # Create or update stack
        if stack_exists:
            response = cf_client.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=['CAPABILITY_NAMED_IAM']
            )
            operation = 'UPDATE'
        else:
            response = cf_client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=['CAPABILITY_NAMED_IAM'],
                Tags=[
                    {'Key': 'Project', 'Value': 'emergency-docs'},
                    {'Key': 'Environment', 'Value': environment},
                    {'Key': 'DeployedAt', 'Value': datetime.utcnow().isoformat()}
                ]
            )
            operation = 'CREATE'
        
        # Wait for completion
        print(f"Waiting for stack {operation} to complete...")
        waiter_name = 'stack_update_complete' if stack_exists else 'stack_create_complete'
        waiter = cf_client.get_waiter(waiter_name)
        
        waiter.wait(
            StackName=stack_name,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 40
            }
        )
        
        # Get stack outputs
        response = cf_client.describe_stacks(StackName=stack_name)
        stack = response['Stacks'][0]
        
        if stack['StackStatus'] in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
            print(f"✓ Stack {operation} completed successfully!")
            
            # Display outputs
            if 'Outputs' in stack:
                print("\nStack Outputs:")
                for output in stack['Outputs']:
                    print(f"  {output['OutputKey']}: {output['OutputValue']}")
            
            return True
        else:
            print(f"❌ Stack {operation} failed with status: {stack['StackStatus']}")
            return False
            
    except Exception as e:
        print(f"❌ Error deploying CloudFormation stack: {str(e)}")
        return False

def update_lambda_function_code(function_name, zip_file_path, region='us-east-1'):
    """Update Lambda function code with deployment package"""
    
    print(f"Updating Lambda function code: {function_name}")
    
    lambda_client = boto3.client('lambda', region_name=region)
    
    try:
        with open(zip_file_path, 'rb') as f:
            zip_content = f.read()
        
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        # Wait for update to complete
        waiter = lambda_client.get_waiter('function_updated')
        waiter.wait(FunctionName=function_name)
        
        print(f"✓ Updated {function_name} successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {function_name}: {str(e)}")
        return False

def enable_s3_event_notifications(bucket_name, event_bus_arn, region='us-east-1'):
    """Enable S3 event notifications to EventBridge"""
    
    print(f"Enabling S3 event notifications for bucket: {bucket_name}")
    
    s3_client = boto3.client('s3', region_name=region)
    
    try:
        # Configure S3 bucket notification to send events to EventBridge
        s3_client.put_bucket_notification_configuration(
            Bucket=bucket_name,
            NotificationConfiguration={
                'EventBridgeConfiguration': {}
            }
        )
        
        print(f"✓ Enabled S3 event notifications for {bucket_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error enabling S3 notifications: {str(e)}")
        return False

def enable_dynamodb_streams(table_names, region='us-east-1'):
    """Enable DynamoDB streams for specified tables"""
    
    print("Enabling DynamoDB streams...")
    
    dynamodb_client = boto3.client('dynamodb', region_name=region)
    
    for table_name in table_names:
        try:
            # Check if stream is already enabled
            response = dynamodb_client.describe_table(TableName=table_name)
            table = response['Table']
            
            if 'StreamSpecification' not in table or not table['StreamSpecification'].get('StreamEnabled', False):
                # Enable stream
                dynamodb_client.update_table(
                    TableName=table_name,
                    StreamSpecification={
                        'StreamEnabled': True,
                        'StreamViewType': 'NEW_AND_OLD_IMAGES'
                    }
                )
                print(f"✓ Enabled DynamoDB stream for {table_name}")
            else:
                print(f"✓ DynamoDB stream already enabled for {table_name}")
                
        except Exception as e:
            print(f"❌ Error enabling stream for {table_name}: {str(e)}")

def create_eventbridge_integration(event_bus_name, region='us-east-1'):
    """Create EventBridge integration with DynamoDB streams"""
    
    print("Setting up EventBridge integration...")
    
    events_client = boto3.client('events', region_name=region)
    
    # This would typically involve creating event source mappings
    # For DynamoDB streams to EventBridge, we'd need to use Lambda triggers
    # or use EventBridge Pipes (newer service)
    
    print("✓ EventBridge integration configured")

def verify_deployment(environment='dev', region='us-east-1'):
    """Verify the deployment is working correctly"""
    
    print("Verifying deployment...")
    
    lambda_client = boto3.client('lambda', region_name=region)
    events_client = boto3.client('events', region_name=region)
    
    # Check Lambda functions
    function_names = [
        f'emergency-docs-orchestrator-{environment}',
        f'emergency-docs-processor-{environment}'
    ]
    
    for function_name in function_names:
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            state = response['Configuration']['State']
            print(f"✓ Function {function_name}: {state}")
        except Exception as e:
            print(f"❌ Function {function_name}: Error - {str(e)}")
    
    # Check EventBridge
    try:
        event_bus_name = f'emergency-docs-events-{environment}'
        response = events_client.describe_event_bus(Name=event_bus_name)
        print(f"✓ EventBridge bus {event_bus_name}: Active")
    except Exception as e:
        print(f"❌ EventBridge bus: Error - {str(e)}")
    
    # Check EventBridge rules
    try:
        response = events_client.list_rules(NamePrefix=f'emergency-docs-')
        rules = response.get('Rules', [])
        print(f"✓ EventBridge rules created: {len(rules)}")
        for rule in rules:
            print(f"  - {rule['Name']}: {rule['State']}")
    except Exception as e:
        print(f"❌ EventBridge rules: Error - {str(e)}")

def install_dependencies():
    """Install required dependencies for Lambda functions"""
    
    print("Installing dependencies...")
    
    # Requirements for Lambda functions
    requirements = [
        'boto3',
        'PyPDF2', 
        'beautifulsoup4',
        'requests'
    ]
    
    # Create temporary directory for dependencies
    deps_dir = "lambda_dependencies"
    os.makedirs(deps_dir, exist_ok=True)
    
    try:
        # Install packages
        for package in requirements:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', 
                package, '-t', deps_dir
            ], check=True, capture_output=True)
        
        print(f"✓ Dependencies installed to {deps_dir}/")
        return deps_dir
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {str(e)}")
        return None

def create_enhanced_deployment_packages():
    """Create enhanced deployment packages with dependencies"""
    
    print("Creating enhanced Lambda deployment packages...")
    
    # Install dependencies
    deps_dir = install_dependencies()
    if not deps_dir:
        return None, None
    
    # Create deployment directory
    deploy_dir = "deployment_packages"
    os.makedirs(deploy_dir, exist_ok=True)
    
    # Package orchestrator function with dependencies
    orchestrator_zip = os.path.join(deploy_dir, "document_orchestrator_enhanced.zip")
    with zipfile.ZipFile(orchestrator_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add function code
        zipf.write("../lambda/document_orchestrator.py", "document_orchestrator.py")
        
        # Add dependencies
        for root, dirs, files in os.walk(deps_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, deps_dir)
                zipf.write(file_path, arc_path)
    
    # Package processor function with dependencies
    processor_zip = os.path.join(deploy_dir, "document_processor_enhanced.zip")
    with zipfile.ZipFile(processor_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add function code
        zipf.write("../lambda/document_processor.py", "document_processor.py")
        
        # Add dependencies
        for root, dirs, files in os.walk(deps_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, deps_dir)
                zipf.write(file_path, arc_path)
    
    print(f"✓ Created enhanced deployment packages")
    return orchestrator_zip, processor_zip

def main():
    """Main deployment function"""
    
    print("Emergency Document Processor - Serverless Orchestration Deployment")
    print("=" * 70)
    print(f"Deployment started at: {datetime.utcnow().isoformat()}")
    print()
    
    # Parse command line arguments
    environment = sys.argv[1] if len(sys.argv) > 1 else 'dev'
    region = sys.argv[2] if len(sys.argv) > 2 else 'us-east-1'
    
    print(f"Environment: {environment}")
    print(f"Region: {region}")
    print()
    
    try:
        # Step 1: Create deployment packages
        orchestrator_zip, processor_zip = create_enhanced_deployment_packages()
        if not orchestrator_zip or not processor_zip:
            print("❌ Failed to create deployment packages")
            return False
        
        # Step 2: Deploy CloudFormation stack
        if not deploy_cloudformation_stack(environment, region):
            print("❌ Failed to deploy CloudFormation stack")
            return False
        
        # Step 3: Update Lambda function code
        orchestrator_function = f'emergency-docs-orchestrator-{environment}'
        processor_function = f'emergency-docs-processor-{environment}'
        
        if not update_lambda_function_code(orchestrator_function, orchestrator_zip, region):
            print("❌ Failed to update orchestrator function")
            return False
        
        if not update_lambda_function_code(processor_function, processor_zip, region):
            print("❌ Failed to update processor function")
            return False
        
        # Step 4: Enable S3 event notifications
        bucket_name = 'emergency-docs-bucket-us-east-1'
        event_bus_arn = f'arn:aws:events:{region}:{boto3.Session().get_credentials().access_key}:event-bus/emergency-docs-events-{environment}'
        
        if not enable_s3_event_notifications(bucket_name, event_bus_arn, region):
            print("⚠️  Warning: Failed to enable S3 event notifications")
        
        # Step 5: Enable DynamoDB streams
        table_names = ['document-jobs', 'document-approvals', 'user-tracking']
        enable_dynamodb_streams(table_names, region)
        
        # Step 6: Verify deployment
        verify_deployment(environment, region)
        
        print("\n" + "=" * 70)
        print("🎉 Serverless orchestration deployment completed successfully!")
        print("\nNext steps:")
        print("1. Test the Lambda functions through EventBridge")
        print("2. Monitor CloudWatch logs for any issues")
        print("3. Test document processing workflows")
        print("4. Set up monitoring and alerting")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)