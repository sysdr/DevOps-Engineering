#!/bin/bash

echo "✅ Verifying Day 21: Integration Assessment Setup"
echo "=============================================="

# Check directory structure
echo "📁 Checking directory structure..."
REQUIRED_DIRS=(
    "src/integration_tests"
    "src/load_testing" 
    "src/monitoring"
    "src/documentation"
    "src/cost_analysis"
    "frontend/src/components"
    "frontend/src/pages"
    "tests"
    "docs"
    "config"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir"
    else
        echo "❌ $dir (missing)"
    fi
done

# Check required files
echo ""
echo "📄 Checking required files..."
REQUIRED_FILES=(
    "src/main.py"
    "src/integration_tests/test_orchestrator.py"
    "src/load_testing/load_generator.py"
    "src/monitoring/performance_monitor.py"
    "src/documentation/doc_generator.py"
    "src/cost_analysis/cost_analyzer.py"
    "frontend/src/App.js"
    "frontend/package.json"
    "requirements.txt"
    "Dockerfile"
    "docker-compose.yml"
    "start.sh"
    "stop.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
    fi
done

# Check if Python dependencies are installed
echo ""
echo "🐍 Checking Python environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment found"
    
    # Check key dependencies
    python -c "import fastapi; print('✅ FastAPI installed')" 2>/dev/null || echo "❌ FastAPI not installed"
    python -c "import pytest; print('✅ Pytest installed')" 2>/dev/null || echo "❌ Pytest not installed"
    python -c "import aiohttp; print('✅ aiohttp installed')" 2>/dev/null || echo "❌ aiohttp not installed"
else
    echo "❌ Virtual environment not found"
fi

echo ""
echo "📊 File counts:"
echo "Python files: $(find src -name '*.py' | wc -l)"
echo "JavaScript files: $(find frontend/src -name '*.js' | wc -l)"
echo "Test files: $(find tests -name '*.py' | wc -l)"

echo ""
echo "🔍 Verification completed!"
