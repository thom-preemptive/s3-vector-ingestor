#!/usr/bin/env python3
"""
Deploy Queue Infrastructure

This script deploys the job queue infrastructure using CloudFormation.
It sets up SQS queues, DynamoDB tables, CloudWatch monitoring, and IAM roles.
"""

import boto3
import json
import os
import time
import sys
from typing import Dict, Any, Optional

class QueueInfrastructureDeployer:
    def __init__(self, region: str = 'us-east-1', environment: str = 'dev'):
        self.region = region
        self.environment = environment
        self.cloudformation = boto3.client('cloudformation', region_name=region)
        self.stack_name = f'{environment}-emergency-docs-queue-infrastructure'
        
    def deploy_infrastructure(self, s3_bucket_name: str) -> bool:
        """Deploy the queue infrastructure stack"""
        try:
            template_path = os.path.join(os.path.dirname(__file__), 'queue-infrastructure.yaml')
            
            with open(template_path, 'r') as f:
                template_body = f.read()
            
            parameters = [
                {
                    'ParameterKey': 'Environment',
                    'ParameterValue': self.environment
                },
                {
                    'ParameterKey': 'S3BucketName',
                    'ParameterValue': s3_bucket_name
                }
            ]
            
            # Check if stack exists
            stack_exists = self._stack_exists()
            
            if stack_exists:
                print(f"Updating existing stack: {self.stack_name}")
                response = self.cloudformation.update_stack(
                    StackName=self.stack_name,
                    TemplateBody=template_body,
                    Parameters=parameters,
                    Capabilities=['CAPABILITY_NAMED_IAM']
                )
                operation = 'UPDATE'
            else:
                print(f"Creating new stack: {self.stack_name}")
                response = self.cloudformation.create_stack(
                    StackName=self.stack_name,
                    TemplateBody=template_body,
                    Parameters=parameters,
                    Capabilities=['CAPABILITY_NAMED_IAM'],
                    EnableTerminationProtection=True,
                    Tags=[
                        {'Key': 'Environment', 'Value': self.environment},
                        {'Key': 'Service', 'Value': 'EmergencyDocProcessor'},
                        {'Key': 'Component', 'Value': 'QueueInfrastructure'}
                    ]
                )
                operation = 'CREATE'
            
            stack_id = response['StackId']
            print(f"Stack {operation} initiated. Stack ID: {stack_id}")
            
            # Wait for stack operation to complete
            success = self._wait_for_stack_completion(operation)
            
            if success:
                print(f"Stack {operation.lower()} completed successfully!")
                self._print_stack_outputs()
                return True
            else:
                print(f"Stack {operation.lower()} failed!")
                self._print_stack_events()
                return False
                
        except Exception as e:
            print(f"Error deploying infrastructure: {str(e)}")
            return False
    
    def _stack_exists(self) -> bool:
        """Check if the CloudFormation stack exists"""
        try:
            self.cloudformation.describe_stacks(StackName=self.stack_name)
            return True
        except self.cloudformation.exceptions.ClientError:
            return False
    
    def _wait_for_stack_completion(self, operation: str) -> bool:
        """Wait for stack operation to complete"""
        if operation == 'CREATE':
            success_status = 'CREATE_COMPLETE'
            failure_statuses = ['CREATE_FAILED', 'ROLLBACK_COMPLETE', 'ROLLBACK_FAILED']
        else:  # UPDATE
            success_status = 'UPDATE_COMPLETE'
            failure_statuses = ['UPDATE_FAILED', 'UPDATE_ROLLBACK_COMPLETE', 'UPDATE_ROLLBACK_FAILED']
        
        print("Waiting for stack operation to complete...")
        start_time = time.time()
        
        while True:
            try:
                response = self.cloudformation.describe_stacks(StackName=self.stack_name)
                stack_status = response['Stacks'][0]['StackStatus']
                
                elapsed = int(time.time() - start_time)
                print(f"Stack status: {stack_status} (elapsed: {elapsed}s)")
                
                if stack_status == success_status:
                    return True
                elif stack_status in failure_statuses:
                    return False
                elif stack_status.endswith('_IN_PROGRESS'):
                    time.sleep(30)  # Wait 30 seconds before checking again
                else:
                    print(f"Unexpected stack status: {stack_status}")
                    return False
                    
            except Exception as e:
                print(f"Error checking stack status: {str(e)}")
                return False
    
    def _print_stack_outputs(self):
        """Print stack outputs"""
        try:
            response = self.cloudformation.describe_stacks(StackName=self.stack_name)
            outputs = response['Stacks'][0].get('Outputs', [])
            
            if outputs:
                print("\n=== Stack Outputs ===")
                for output in outputs:
                    print(f"{output['OutputKey']}: {output['OutputValue']}")
                    if 'Description' in output:
                        print(f"  Description: {output['Description']}")
                print()
            
        except Exception as e:
            print(f"Error retrieving stack outputs: {str(e)}")
    
    def _print_stack_events(self):
        """Print recent stack events"""
        try:
            response = self.cloudformation.describe_stack_events(StackName=self.stack_name)
            events = response['StackEvents'][:10]  # Last 10 events
            
            print("\n=== Recent Stack Events ===")
            for event in events:
                timestamp = event['Timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                resource_status = event.get('ResourceStatus', 'N/A')
                resource_type = event.get('ResourceType', 'N/A')
                logical_id = event.get('LogicalResourceId', 'N/A')
                reason = event.get('ResourceStatusReason', '')
                
                print(f"{timestamp} - {logical_id} ({resource_type}): {resource_status}")
                if reason:
                    print(f"  Reason: {reason}")
            print()
            
        except Exception as e:
            print(f"Error retrieving stack events: {str(e)}")
    
    def get_queue_urls(self) -> Dict[str, str]:
        """Get SQS queue URLs from stack outputs"""
        try:
            response = self.cloudformation.describe_stacks(StackName=self.stack_name)
            outputs = response['Stacks'][0].get('Outputs', [])
            
            queue_urls = {}
            for output in outputs:
                key = output['OutputKey']
                value = output['OutputValue']
                
                if key.endswith('QueueUrl'):
                    queue_name = key.replace('QueueUrl', '').lower()
                    queue_urls[queue_name] = value
            
            return queue_urls
            
        except Exception as e:
            print(f"Error retrieving queue URLs: {str(e)}")
            return {}
    
    def get_table_names(self) -> Dict[str, str]:
        """Get DynamoDB table names from stack outputs"""
        try:
            response = self.cloudformation.describe_stacks(StackName=self.stack_name)
            outputs = response['Stacks'][0].get('Outputs', [])
            
            table_names = {}
            for output in outputs:
                key = output['OutputKey']
                value = output['OutputValue']
                
                if key.endswith('TableName'):
                    table_key = key.replace('TableName', '').lower()
                    table_names[table_key] = value
            
            return table_names
            
        except Exception as e:
            print(f"Error retrieving table names: {str(e)}")
            return {}
    
    def setup_environment_variables(self) -> Dict[str, str]:
        """Get environment variables for application configuration"""
        try:
            queue_urls = self.get_queue_urls()
            table_names = self.get_table_names()
            
            env_vars = {
                'DOC_PROCESSING_QUEUE': queue_urls.get('documentprocessing', ''),
                'APPROVAL_QUEUE': queue_urls.get('approvalworkflow', ''),
                'MAINTENANCE_QUEUE': queue_urls.get('maintenance', ''),
                'QUEUE_JOBS_TABLE': table_names.get('queuejobs', ''),
                'AWS_REGION': self.region,
                'ENVIRONMENT': self.environment
            }
            
            # Remove empty values
            env_vars = {k: v for k, v in env_vars.items() if v}
            
            print("\n=== Environment Variables ===")
            for key, value in env_vars.items():
                print(f"export {key}='{value}'")
            print()
            
            return env_vars
            
        except Exception as e:
            print(f"Error setting up environment variables: {str(e)}")
            return {}
    
    def create_dashboard_config(self) -> Dict[str, Any]:
        """Create dashboard configuration for monitoring"""
        try:
            queue_urls = self.get_queue_urls()
            
            dashboard_config = {
                'region': self.region,
                'environment': self.environment,
                'queues': {
                    'document_processing': queue_urls.get('documentprocessing', ''),
                    'approval_workflow': queue_urls.get('approvalworkflow', ''),
                    'maintenance': queue_urls.get('maintenance', '')
                },
                'cloudwatch_namespace': 'EmergencyDocs/JobQueue',
                'refresh_interval': 30  # seconds
            }
            
            # Save config to file
            config_path = os.path.join(os.path.dirname(__file__), 'dashboard-config.json')
            with open(config_path, 'w') as f:
                json.dump(dashboard_config, f, indent=2)
            
            print(f"Dashboard configuration saved to: {config_path}")
            return dashboard_config
            
        except Exception as e:
            print(f"Error creating dashboard config: {str(e)}")
            return {}
    
    def test_infrastructure(self) -> bool:
        """Test the deployed infrastructure"""
        try:
            print("Testing deployed infrastructure...")
            
            # Test SQS queues
            sqs = boto3.client('sqs', region_name=self.region)
            queue_urls = self.get_queue_urls()
            
            for queue_name, queue_url in queue_urls.items():
                if queue_url:
                    try:
                        response = sqs.get_queue_attributes(
                            QueueUrl=queue_url,
                            AttributeNames=['QueueArn', 'VisibilityTimeoutSeconds']
                        )
                        print(f"✓ Queue {queue_name} is accessible")
                    except Exception as e:
                        print(f"✗ Queue {queue_name} test failed: {str(e)}")
                        return False
            
            # Test DynamoDB tables
            dynamodb = boto3.client('dynamodb', region_name=self.region)
            table_names = self.get_table_names()
            
            for table_key, table_name in table_names.items():
                if table_name:
                    try:
                        response = dynamodb.describe_table(TableName=table_name)
                        table_status = response['Table']['TableStatus']
                        if table_status == 'ACTIVE':
                            print(f"✓ Table {table_name} is active")
                        else:
                            print(f"✗ Table {table_name} status: {table_status}")
                            return False
                    except Exception as e:
                        print(f"✗ Table {table_name} test failed: {str(e)}")
                        return False
            
            print("✓ Infrastructure test completed successfully!")
            return True
            
        except Exception as e:
            print(f"Error testing infrastructure: {str(e)}")
            return False
    
    def delete_stack(self) -> bool:
        """Delete the CloudFormation stack"""
        try:
            if not self._stack_exists():
                print(f"Stack {self.stack_name} does not exist")
                return True
            
            print(f"Deleting stack: {self.stack_name}")
            
            # Disable termination protection first
            self.cloudformation.update_termination_protection(
                StackName=self.stack_name,
                EnableTerminationProtection=False
            )
            
            self.cloudformation.delete_stack(StackName=self.stack_name)
            
            # Wait for deletion to complete
            print("Waiting for stack deletion to complete...")
            start_time = time.time()
            
            while True:
                try:
                    response = self.cloudformation.describe_stacks(StackName=self.stack_name)
                    stack_status = response['Stacks'][0]['StackStatus']
                    
                    elapsed = int(time.time() - start_time)
                    print(f"Stack status: {stack_status} (elapsed: {elapsed}s)")
                    
                    if stack_status == 'DELETE_COMPLETE':
                        print("Stack deleted successfully!")
                        return True
                    elif stack_status == 'DELETE_FAILED':
                        print("Stack deletion failed!")
                        self._print_stack_events()
                        return False
                    elif stack_status == 'DELETE_IN_PROGRESS':
                        time.sleep(30)
                    else:
                        print(f"Unexpected stack status: {stack_status}")
                        return False
                        
                except self.cloudformation.exceptions.ClientError as e:
                    if 'does not exist' in str(e):
                        print("Stack deleted successfully!")
                        return True
                    else:
                        raise
                        
        except Exception as e:
            print(f"Error deleting stack: {str(e)}")
            return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy Queue Infrastructure')
    parser.add_argument('--environment', '-e', default='dev', help='Environment name')
    parser.add_argument('--region', '-r', default='us-east-1', help='AWS region')
    parser.add_argument('--s3-bucket', '-b', required=True, help='S3 bucket name for document storage')
    parser.add_argument('--delete', action='store_true', help='Delete the stack instead of deploying')
    parser.add_argument('--test', action='store_true', help='Test the deployed infrastructure')
    
    args = parser.parse_args()
    
    deployer = QueueInfrastructureDeployer(
        region=args.region,
        environment=args.environment
    )
    
    if args.delete:
        success = deployer.delete_stack()
        sys.exit(0 if success else 1)
    
    if args.test:
        success = deployer.test_infrastructure()
        sys.exit(0 if success else 1)
    
    # Deploy infrastructure
    success = deployer.deploy_infrastructure(args.s3_bucket)
    
    if success:
        # Set up environment variables and configuration
        deployer.setup_environment_variables()
        deployer.create_dashboard_config()
        
        # Test the deployment
        if deployer.test_infrastructure():
            print("\n🎉 Queue infrastructure deployment completed successfully!")
            print("\nNext steps:")
            print("1. Update your application configuration with the environment variables above")
            print("2. Deploy your application with the new queue service")
            print("3. Check the CloudWatch dashboard for monitoring")
        else:
            print("\n⚠️  Infrastructure deployed but tests failed. Check the configuration.")
            sys.exit(1)
    else:
        print("\n❌ Infrastructure deployment failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()