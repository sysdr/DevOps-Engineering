#!/bin/bash
# Script to verify and create missing files from setup.sh

set -e

PROJECT_DIR="$(pwd)/secrets-management-system"
cd "$PROJECT_DIR"

echo "=== Verifying and Creating Missing Files ==="

# List of expected files
declare -A files
files[requirements.txt]="cat > requirements.txt << 'EOF'
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.3
httpx==0.26.0
python-multipart==0.0.6
hvac==2.1.0
cryptography==42.0.0
pytest==7.4.4
pytest-asyncio==0.23.3
EOF"

# Check and create files
check_and_create() {
    local filepath=$1
    if [ ! -f "$filepath" ]; then
        echo "Creating missing file: $filepath"
        mkdir -p "$(dirname "$filepath")"
        return 1
    else
        echo "✓ $filepath exists"
        return 0
    fi
}

# Since we can't easily recreate all heredocs here, let's just run setup.sh again
# but first let's check if it completed
if [ ! -f "requirements.txt" ] || [ ! -f "backend/main.py" ] || [ ! -f "start.sh" ]; then
    echo "Key files missing. Re-running setup.sh from parent directory..."
    cd ..
    bash setup.sh
else
    echo "All key files exist!"
fi

