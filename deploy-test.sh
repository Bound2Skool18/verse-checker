#!/bin/bash

echo "🚀 Bible Verse Checker - Deployment Test Script"
echo "=============================================="

# Test 1: Check if all required files exist
echo "📋 Checking required files..."
files=("app/main.py" "app/config.py" "requirements.txt" "Dockerfile" "README.md")
all_files_exist=true

for file in "${files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        all_files_exist=false
    fi
done

# Test 2: Check Python environment
echo -e "\n🐍 Checking Python environment..."
if command -v python3 &> /dev/null; then
    echo "✅ Python3 available: $(python3 --version)"
else
    echo "❌ Python3 not found"
    all_files_exist=false
fi

# Test 3: Check virtual environment
echo -e "\n📦 Checking virtual environment..."
if [[ -d ".venv" ]]; then
    echo "✅ Virtual environment exists"
    if [[ -f ".venv/bin/activate" ]]; then
        echo "✅ Virtual environment is properly set up"
    else
        echo "⚠️  Virtual environment may not be properly configured"
    fi
else
    echo "⚠️  No virtual environment found (you'll need to create one)"
fi

# Test 4: Check if dependencies can be imported
echo -e "\n🔧 Testing core dependencies..."
if [[ -f ".venv/bin/activate" ]]; then
    source .venv/bin/activate
    
    dependencies=("fastapi" "uvicorn" "qdrant_client" "sentence_transformers")
    for dep in "${dependencies[@]}"; do
        if python3 -c "import $dep" 2>/dev/null; then
            echo "✅ $dep can be imported"
        else
            echo "❌ $dep cannot be imported"
            all_files_exist=false
        fi
    done
else
    echo "⚠️  Skipping dependency check (no virtual environment)"
fi

# Test 5: Check data files
echo -e "\n📚 Checking data files..."
if [[ -f "data/bible.json" ]]; then
    verses=$(python3 -c "import json; data=json.load(open('data/bible.json')); print(len(data))" 2>/dev/null)
    echo "✅ Bible data exists with $verses verses"
else
    echo "⚠️  Bible data file not found"
fi

if [[ -d "qdrant_data" ]]; then
    echo "✅ Qdrant data directory exists"
else
    echo "⚠️  Qdrant data directory not found (will be created on first run)"
fi

# Test 6: Check Docker files
echo -e "\n🐳 Checking Docker configuration..."
if [[ -f "Dockerfile" ]]; then
    echo "✅ Dockerfile exists"
else
    echo "❌ Dockerfile missing"
fi

if [[ -f "docker-compose.yml" ]]; then
    echo "✅ Docker Compose file exists"
else
    echo "❌ docker-compose.yml missing"
fi

# Final assessment
echo -e "\n🎯 DEPLOYMENT READINESS ASSESSMENT"
echo "=================================="

if [[ "$all_files_exist" == true ]]; then
    echo "🟢 STATUS: READY FOR DEPLOYMENT!"
    echo ""
    echo "Your options:"
    echo "1. 🐳 Docker: docker build -t verse-checker . && docker run -p 8000:8000 verse-checker"
    echo "2. 🖥️  Local: source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"
    echo "3. ☁️  Cloud: Push to GitHub and deploy to Heroku/Railway/Render"
    echo ""
    echo "📖 See DEPLOYMENT.md for complete instructions!"
else
    echo "🟡 STATUS: NEEDS ATTENTION"
    echo ""
    echo "Fix the issues above, then you'll be ready to deploy!"
fi

echo ""
echo "🏁 Test completed!"