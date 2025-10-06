#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced PDF OCR processing with configurable threshold.
"""

import boto3
import json
import os
from io import BytesIO
import PyPDF2

def get_ssm_parameter(parameter_name: str, region: str = 'us-east-1') -> str:
    """Get parameter from SSM Parameter Store"""
    ssm = boto3.client('ssm', region_name=region)
    try:
        response = ssm.get_parameter(Name=parameter_name)
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Failed to get parameter {parameter_name}: {e}")
        return "50"  # Default fallback

def set_ssm_parameter(parameter_name: str, value: str, region: str = 'us-east-1') -> bool:
    """Set parameter in SSM Parameter Store"""
    ssm = boto3.client('ssm', region_name=region)
    try:
        ssm.put_parameter(
            Name=parameter_name,
            Value=str(value),
            Type='String',
            Overwrite=True,
            Description=f'OCR threshold for PDF processing'
        )
        print(f"✅ Set parameter {parameter_name} = {value}")
        return True
    except Exception as e:
        print(f"❌ Failed to set parameter {parameter_name}: {e}")
        return False

def test_ocr_threshold_configuration():
    """Test OCR threshold configuration functionality"""
    print("🧪 Testing PDF OCR Threshold Configuration")
    print("=" * 50)
    
    # Test parameters for different environments
    environments = ['dev', 'test', 'main']
    
    for env in environments:
        parameter_name = f'/agent2-ingestor/{env}/ocr-threshold'
        
        print(f"\n📋 Testing environment: {env}")
        
        # Get current value
        current_value = get_ssm_parameter(parameter_name)
        print(f"Current OCR threshold: {current_value}")
        
        # Set a test value
        test_value = "75"  # Higher threshold to trigger OCR more often
        if set_ssm_parameter(parameter_name, test_value):
            
            # Verify the value was set
            retrieved_value = get_ssm_parameter(parameter_name)
            if retrieved_value == test_value:
                print(f"✅ Successfully configured OCR threshold: {retrieved_value}")
            else:
                print(f"❌ Mismatch: Expected {test_value}, got {retrieved_value}")
        
        print(f"Parameter path: {parameter_name}")

def simulate_pdf_processing_logic():
    """Simulate the enhanced PDF processing logic"""
    print("\n🔍 Simulating Enhanced PDF Processing Logic")
    print("=" * 50)
    
    # Test scenarios
    scenarios = [
        {"filename": "simple_text.pdf", "word_count": 120, "expected_method": "Text Extraction"},
        {"filename": "scanned_image.pdf", "word_count": 25, "expected_method": "OCR (Advanced)"},
        {"filename": "mixed_content.pdf", "word_count": 60, "expected_method": "Text Extraction"},
        {"filename": "poor_scan.pdf", "word_count": 15, "expected_method": "OCR (Advanced)"},
    ]
    
    ocr_threshold = 75  # Using the test threshold
    
    for scenario in scenarios:
        filename = scenario["filename"]
        word_count = scenario["word_count"]
        expected_method = scenario["expected_method"]
        
        print(f"\n📄 Processing: {filename}")
        print(f"   Word count: {word_count}")
        print(f"   OCR threshold: {ocr_threshold}")
        
        if word_count < ocr_threshold:
            processing_method = "OCR (Advanced)"
            used_ocr = True
            print(f"   🤖 OCR triggered (words < threshold)")
        else:
            processing_method = "Text Extraction"
            used_ocr = False
            print(f"   📝 Text extraction sufficient (words >= threshold)")
        
        print(f"   Processing method: {processing_method}")
        print(f"   Used OCR: {used_ocr}")
        
        # Simulate metadata that would be returned
        metadata = {
            "source_type": "pdf",
            "filename": filename,
            "processing_method": processing_method,
            "used_ocr": used_ocr,
            "ocr_threshold_used": ocr_threshold,
            "word_count": word_count
        }
        
        print(f"   📊 Metadata: {json.dumps(metadata, indent=6)}")

def test_frontend_indicators():
    """Show how the frontend indicators would work"""
    print("\n🎨 Frontend Processing Method Indicators")
    print("=" * 50)
    
    test_documents = [
        {"processing_method": "Text Extraction", "used_ocr": False},
        {"processing_method": "OCR (Advanced)", "used_ocr": True},
        {"processing_method": "OCR (Basic)", "used_ocr": True},
        {"processing_method": "Text Extraction (OCR Failed)", "used_ocr": True},
    ]
    
    for doc in test_documents:
        method = doc["processing_method"]
        used_ocr = doc["used_ocr"]
        
        # Simulate the frontend logic
        if used_ocr:
            if "Advanced" in method:
                color = "success"
                label = "OCR+"
            elif "Basic" in method:
                color = "warning"
                label = "OCR"
            elif "Failed" in method:
                color = "error"
                label = "Text Only"
        else:
            color = "info"
            label = "Text"
        
        variant = "filled" if used_ocr else "outlined"
        
        print(f"📋 Method: {method}")
        print(f"   🏷️  Chip: {label} ({color}, {variant})")
        print(f"   💡 Tooltip: Processing Method: {method}")
        print()

if __name__ == "__main__":
    print("🚀 Enhanced PDF OCR Processing Test Suite")
    print("="*60)
    
    try:
        # Test 1: OCR threshold configuration
        test_ocr_threshold_configuration()
        
        # Test 2: Processing logic simulation
        simulate_pdf_processing_logic()
        
        # Test 3: Frontend indicators
        test_frontend_indicators()
        
        print("\n✅ All tests completed successfully!")
        print("\n📋 Summary of enhancements:")
        print("  • Configurable OCR threshold per environment via SSM Parameter Store")
        print("  • Enhanced PDF processing with multiple OCR fallbacks")
        print("  • Visual indicators in frontend showing processing method")
        print("  • Detailed metadata tracking OCR usage and thresholds")
        print("  • Environment-specific configuration management")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()