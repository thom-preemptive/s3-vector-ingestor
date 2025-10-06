#!/usr/bin/env python3
"""
Test script to verify the Clear Tables fix works correctly.
This directly tests the aws_services.py clear_environment_tables method.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.aws_services import clear_environment_tables

def test_clear_tables():
    """Test the clear tables functionality"""
    print("Testing Clear Tables functionality...")
    
    # Set environment to DEV for testing
    os.environ['ENVIRONMENT'] = 'dev'
    
    try:
        # This should find and clear tables with names like agent2_ingestor_jobs_dev
        result = clear_environment_tables('dev')
        print(f"Clear tables result: {result}")
        
        if result['tables_cleared'] > 0:
            print(f"✅ SUCCESS: Cleared {result['tables_cleared']} tables")
            for table in result['tables']:
                print(f"   - {table}")
        else:
            print("❌ ISSUE: No tables were cleared")
            print("Available tables:")
            
            # Let's also list tables to see what's available
            import boto3
            dynamodb = boto3.client('dynamodb', region_name='us-east-1')
            response = dynamodb.list_tables()
            for table_name in response['TableNames']:
                print(f"   - {table_name}")
                if 'dev' in table_name:
                    print(f"     ↳ This should have been cleared!")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_clear_tables()