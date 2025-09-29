#!/bin/bash

# Emergency Document Processor - Quick Deployment Test
echo "🚀 Emergency Document Processor - Quick Test"
echo "============================================="

# Test 1: Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "infrastructure" ]; then
    echo "❌ Please run this script from the project root directory"
    echo "   The directory should contain 'backend' and 'infrastructure' folders"
    exit 1
fi

echo "✅ Project structure verified"

# Test 2: Check Python environment
echo ""
echo "🐍 Testing Python Environment..."
if python --version &> /dev/null; then
    echo "✅ Python: $(python --version)"
else
    echo "❌ Python not found"
    exit 1
fi

# Test 3: Check virtual environment
if [ -d ".venv" ]; then
    echo "✅ Virtual environment found at .venv/"
    if [ "$VIRTUAL_ENV" = "" ]; then
        echo "⚠️  Virtual environment not activated"
        echo "   Run: source .venv/bin/activate"
    else
        echo "✅ Virtual environment activated: $VIRTUAL_ENV"
    fi
else
    echo "⚠️  Virtual environment not found"
    echo "   Create with: python -m venv .venv"
fi

# Test 4: Check AWS CLI
echo ""
echo "☁️  Testing AWS Configuration..."
if aws --version &> /dev/null; then
    echo "✅ AWS CLI: $(aws --version)"
    
    # Test AWS credentials
    if aws sts get-caller-identity &> /dev/null; then
        echo "✅ AWS Credentials configured"
        aws sts get-caller-identity --output table
    else
        echo "❌ AWS Credentials not configured"
        echo "   Run: aws configure"
    fi
else
    echo "❌ AWS CLI not found"
    echo "   Install from: https://aws.amazon.com/cli/"
fi

# Test 5: Check if backend server is running
echo ""
echo "🌐 Testing Backend Server..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend server running on port 8000"
    echo "   Health check: $(curl -s http://localhost:8000/health | head -1)"
else
    echo "❌ Backend server not running"
    echo "   Start with: cd backend && python main.py"
fi

# Test 6: Check dependencies
echo ""
echo "📦 Testing Dependencies..."
cd backend

if [ -f "requirements.txt" ]; then
    echo "✅ Requirements file found"
    
    # Check if critical packages are installed
    python -c "
try:
    import fastapi, boto3, uvicorn
    print('✅ Core packages (fastapi, boto3, uvicorn) installed')
except ImportError as e:
    print(f'❌ Missing packages: {e}')
    print('   Install with: pip install -r requirements.txt')
" 2>/dev/null
else
    echo "❌ requirements.txt not found"
fi

cd ..

# Test 7: Check infrastructure scripts
echo ""
echo "🏗️  Testing Infrastructure Scripts..."
if [ -f "infrastructure/setup_aws.py" ]; then
    echo "✅ Infrastructure scripts found"
    
    # Test if scripts are executable
    python infrastructure/setup_aws.py --help &> /dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Infrastructure scripts are runnable"
    else
        echo "⚠️  Infrastructure scripts may have issues"
    fi
else
    echo "❌ Infrastructure scripts not found"
fi

# Summary
echo ""
echo "============================================="
echo "📋 QUICK TEST SUMMARY"
echo "============================================="
echo ""
echo "🎯 To deploy the system:"
echo "   1. Activate virtual env: source .venv/bin/activate"
echo "   2. Install dependencies: pip install -r backend/requirements.txt"
echo "   3. Configure AWS: aws configure"
echo "   4. Deploy infrastructure: cd infrastructure && python setup_aws.py"
echo "   5. Start backend: cd backend && python main.py"
echo ""
echo "📖 For detailed deployment instructions, see DEPLOYMENT_GUIDE.md"
echo ""
echo "🧪 To run the comprehensive test: python test_deployment.py"