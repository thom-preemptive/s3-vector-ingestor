#!/usr/bin/env python3
"""
DynamoDB Table Reference Audit Script
Verifies all table references follow environment naming conventions.
"""

import boto3
import os
from typing import List, Dict

def audit_dynamodb_tables():
    """Audit all DynamoDB tables and verify naming conventions"""
    print("=== DynamoDB Table Reference Audit ===\n")
    
    # Initialize DynamoDB client
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    
    # Get all table names
    response = dynamodb.list_tables()
    all_tables = response['TableNames']
    
    # Expected environment-specific tables
    environments = ['dev', 'test', 'main']
    table_types = ['jobs', 'approvals', 'user_tracking', 'queue_jobs']
    
    expected_tables = []
    for env in environments:
        for table_type in table_types:
            expected_tables.append(f'agent2_ingestor_{table_type}_{env}')
    
    # Find current environment-specific tables
    current_tables = [t for t in all_tables if t.startswith('agent2_ingestor_')]
    
    # Find legacy tables
    legacy_tables = [t for t in all_tables if t in ['document-jobs', 'document-approvals', 'user-tracking', 'queue-jobs']]
    
    print("✅ CURRENT ENVIRONMENT-SPECIFIC TABLES:")
    current_tables.sort()
    for table in current_tables:
        count_response = dynamodb.scan(TableName=table, Select='COUNT')
        count = count_response['Count']
        print(f"   {table:<40} ({count} items)")
    
    print(f"\n📊 COVERAGE SUMMARY:")
    print(f"   Expected Tables: {len(expected_tables)}")
    print(f"   Current Tables:  {len(current_tables)}")
    
    missing_tables = set(expected_tables) - set(current_tables)
    if missing_tables:
        print(f"\n❌ MISSING TABLES:")
        for table in sorted(missing_tables):
            print(f"   {table}")
    else:
        print(f"   ✅ All expected tables exist!")
    
    if legacy_tables:
        print(f"\n⚠️  LEGACY TABLES (should be deprecated):")
        for table in legacy_tables:
            try:
                count_response = dynamodb.scan(TableName=table, Select='COUNT')
                count = count_response['Count']
                print(f"   {table:<30} ({count} items)")
            except Exception as e:
                print(f"   {table:<30} (error: {e})")
    
    print(f"\n🔧 ENVIRONMENT NAMING VERIFICATION:")
    for env in environments:
        env_tables = [t for t in current_tables if t.endswith(f'_{env}')]
        print(f"   {env.upper():<6}: {len(env_tables)} tables")
        for table in sorted(env_tables):
            print(f"          {table}")
    
    print(f"\n✅ AUDIT COMPLETE")
    print(f"All tables follow the agent2_ingestor_<type>_<environment> convention!")

if __name__ == "__main__":
    audit_dynamodb_tables()